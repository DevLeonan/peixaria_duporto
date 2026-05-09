from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import json
import csv
import mercadopago # NOVO: Motor do Mercado Pago
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import localtime, now
from datetime import timedelta
from urllib.parse import quote  # Usado para formatar o texto do WhatsApp
from django.db.models import Sum, ProtectedError
from django.views.decorators.csrf import csrf_exempt # NOVO: Necessário para o Webhook funcionar
from .models import LeadRestaurante, CortePescado, Pedido, ItemPedido
import urllib.request
import urllib.parse


# ==========================================
# CONFIGURAÇÃO MERCADO PAGO (Sua Chave Mestra)
# ==========================================
sdk = mercadopago.SDK("APP_USR-5402725203039388-020123-10a75c260cf12f6663994256fc156b5d-1365742803")

def pagina_captura(request):
    if request.method == "POST":
        nome_digitado = request.POST.get("nome_restaurante")
        cnpj_digitado = request.POST.get("cnpj")
        whatsapp_digitado = request.POST.get("whatsapp")
        
        lead, created = LeadRestaurante.objects.get_or_create(
            cnpj=cnpj_digitado,
            defaults={
                'whatsapp': whatsapp_digitado,
                'nome_restaurante': nome_digitado
            }
        )
        
        if not created and nome_digitado:
            lead.nome_restaurante = nome_digitado
            lead.whatsapp = whatsapp_digitado
            lead.save()
        
        return redirect('catalogo_precos', token=lead.token_acesso)
        
    return render(request, 'isca.html')

def catalogo_precos(request, token):
    lead = LeadRestaurante.objects.filter(token_acesso=token).first()
    
    if not lead:
        return redirect('captura')

    cortes = CortePescado.objects.filter(disponivel=True)
    return render(request, 'catalogo.html', {'cortes': cortes, 'lead': lead})

@login_required
def painel_interno(request):
    todos_os_leads = LeadRestaurante.objects.all().order_by('-data_cadastro')
    total_leads = todos_os_leads.count()
    pedidos = Pedido.objects.all().order_by('-data_pedido').prefetch_related('itens', 'itens__corte')
    
    hoje = now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    
    faturamento_hoje = 0
    faturamento_semana = 0
    faturamento_mes = 0
    pendente_total = 0
    
    pedidos_pendentes = []
    pedidos_pagos = []
    
    for p in pedidos:
        data_local = localtime(p.data_pedido).date()
        
        if p.status == 'PAGO':
            pedidos_pagos.append(p)
            if data_local == hoje:
                faturamento_hoje += p.valor_total
            if data_local >= inicio_semana:
                faturamento_semana += p.valor_total
            if data_local >= inicio_mes:
                faturamento_mes += p.valor_total
                
        elif p.status == 'PENDENTE':
            pedidos_pendentes.append(p)
            pendente_total += p.valor_total

    # Gráficos
    top_itens = ItemPedido.objects.filter(pedido__status='PAGO').values('corte__nome').annotate(total_kg=Sum('quantidade_kg')).order_by('-total_kg')[:5]
    nomes_peixes = [item['corte__nome'] for item in top_itens]
    qtd_peixes = [float(item['total_kg']) for item in top_itens]

    dias_grafico = []
    valores_grafico = []
    for i in range(6, -1, -1):
        dia_alvo = hoje - timedelta(days=i)
        soma_dia = Pedido.objects.filter(status='PAGO', data_pedido__date=dia_alvo).aggregate(Sum('valor_total'))['valor_total__sum']
        dias_grafico.append(dia_alvo.strftime("%d/%m"))
        valores_grafico.append(float(soma_dia or 0))
    
    contexto = {
        'leads': todos_os_leads,
        'total_leads': total_leads,
        'faturamento_hoje': faturamento_hoje,
        'faturamento_semana': faturamento_semana,
        'faturamento_mes': faturamento_mes,
        'pendente_total': pendente_total,
        'pedidos_pendentes': pedidos_pendentes,
        'pedidos_pagos': pedidos_pagos,
        'nomes_peixes': json.dumps(nomes_peixes),
        'qtd_peixes': json.dumps(qtd_peixes),
        'dias_grafico': json.dumps(dias_grafico),
        'valores_grafico': json.dumps(valores_grafico),
    }
    return render(request, 'painel_comando.html', contexto)

@login_required
def checar_novos_pedidos(request):
    ultimo_pedido = Pedido.objects.order_by('-id').first()
    ultimo_id = ultimo_pedido.id if ultimo_pedido else 0
    return JsonResponse({'ultimo_id': ultimo_id})

@login_required
def limpar_dados_caixa(request):
    if request.method == "POST":
        try:
            dados = json.loads(request.body)
            periodo = dados.get('periodo')
            senha = dados.get('senha')
            
            if senha != "ZERAR":
                return JsonResponse({'sucesso': False, 'erro': 'Palavra de segurança incorreta. Ação abortada.'})
                
            hoje = now().date()
            if periodo == 'dia':
                Pedido.objects.filter(data_pedido__date=hoje).delete()
            elif periodo == 'mes':
                Pedido.objects.filter(data_pedido__year=hoje.year, data_pedido__month=hoje.month).delete()
            elif periodo == 'tudo':
                Pedido.objects.all().delete()
                
            return JsonResponse({'sucesso': True})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'erro': str(e)})
    return JsonResponse({'sucesso': False})

@login_required
def atualizar_status_pedido(request, pedido_id):
    if request.method == "POST":
        try:
            dados = json.loads(request.body)
            novo_status = dados.get('status')
            
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.status = novo_status
            pedido.save()
            
            return JsonResponse({'sucesso': True})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'erro': str(e)})
            
    return JsonResponse({'sucesso': False, 'erro': 'Método inválido'})

@login_required
def gerenciar_produtos(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        descricao = request.POST.get("descricao")
        preco = request.POST.get("preco_por_kg")
        imagem_url = request.POST.get("imagem_url")
        
        preco_formatado = preco.replace(',', '.')
        
        CortePescado.objects.create(
            nome=nome,
            descricao=descricao,
            preco_por_kg=preco_formatado,
            imagem_url=imagem_url,
            disponivel=True
        )
        return redirect('gerenciar_produtos')
        
    todos_os_cortes = CortePescado.objects.all().order_by('-id')
    return render(request, 'gerenciar_produtos.html', {'produtos': todos_os_cortes})

@login_required
def editar_produto(request, produto_id):
    if request.method == "POST":
        corte = CortePescado.objects.get(id=produto_id)
        corte.nome = request.POST.get("nome")
        corte.descricao = request.POST.get("descricao")
        corte.preco_por_kg = request.POST.get("preco_por_kg").replace(',', '.')
        corte.imagem_url = request.POST.get("imagem_url")
        corte.save()
    return redirect('gerenciar_produtos')

@login_required
def toggle_produto(request, produto_id):
    corte = CortePescado.objects.get(id=produto_id)
    corte.disponivel = not corte.disponivel
    corte.save()
    return redirect('gerenciar_produtos')

@login_required
def excluir_produto(request, produto_id):
    corte = CortePescado.objects.get(id=produto_id)
    try:
        corte.delete()
    except ProtectedError:
        corte.disponivel = False
        corte.save()
    return redirect('gerenciar_produtos')
    
# ==========================================
# FINALIZAR PEDIDO COM PIX INTELIGENTE (CPF/CNPJ) E NTFY
# ==========================================
def finalizar_pedido(request, token):
    if request.method == "POST":
        lead = LeadRestaurante.objects.filter(token_acesso=token).first()
        if not lead:
            return JsonResponse({'sucesso': False, 'erro': 'Cliente não encontrado'})

        try:
            dados = json.loads(request.body)
            carrinho = dados.get('carrinho', [])
            forma_pagamento = dados.get('forma_pagamento', 'PIX')
            
            endereco = dados.get('endereco', '')
            data_entrega = dados.get('data_entrega', None)
            hora_entrega = dados.get('hora_entrega', None)
            
            if not data_entrega: data_entrega = None
            if not hora_entrega: hora_entrega = None

            pedido = Pedido.objects.create(
                lead=lead,
                forma_pagamento=forma_pagamento,
                valor_total=0,
                endereco_entrega=endereco,
                data_entrega=data_entrega,
                hora_entrega=hora_entrega
            )

            total_calculado = 0
            for item in carrinho:
                corte = CortePescado.objects.get(id=item['id'])
                quantidade = float(item['quantidade'])
                total_calculado += float(corte.preco_por_kg) * quantidade
                
                ItemPedido.objects.create(
                    pedido=pedido,
                    corte=corte,
                    quantidade_kg=quantidade,
                    preco_na_epoca=corte.preco_por_kg
                )

            pedido.valor_total = total_calculado
            pedido.save()

            qr_code_base64 = ""
            pix_copia_cola = ""
            
            if forma_pagamento == 'PIX':
                # --- LÓGICA DE IDENTIFICAÇÃO INTELIGENTE ---
                # Remove qualquer ponto, barra ou traço que o cliente possa ter digitado
                id_limpo = lead.cnpj.replace('.', '').replace('/', '').replace('-', '').replace(' ', '').strip()
                
                # O Mercado Pago exige saber se é CPF (11) ou CNPJ (14)
                if len(id_limpo) == 11:
                    tipo_doc = "CPF"
                elif len(id_limpo) == 14:
                    tipo_doc = "CNPJ"
                else:
                    # Se não for nenhum dos dois, o Mercado Pago vai dar erro. 
                    # Aqui evitamos o erro avisando ao cliente antes.
                    pedido.delete()
                    return JsonResponse({'sucesso': False, 'erro': f"O documento '{id_limpo}' é inválido. Digite um CPF ou CNPJ correto."})
                    
                payment_data = {
                    "transaction_amount": float(total_calculado),
                    "description": f"Pedido #{pedido.id} - Peixaria Duporto",
                    "payment_method_id": "pix",
                    "external_reference": str(pedido.id),
                    "payer": {
                        "email": f"comprador_{pedido.id}@peixariaduporto.com.br",
                        "first_name": lead.nome_restaurante or "Cliente",
                        "identification": {
                            "type": tipo_doc, # <--- DINÂMICO: Agora aceita CPF ou CNPJ
                            "number": id_limpo
                        }
                    }
                }
                
                payment_response = sdk.payment().create(payment_data)
                payment = payment_response.get("response", {})
                
                if "point_of_interaction" in payment:
                    pix_copia_cola = payment["point_of_interaction"]["transaction_data"]["qr_code"]
                    qr_code_base64 = payment["point_of_interaction"]["transaction_data"]["qr_code_base64"]
                else:
                    # Captura o erro detalhado para você saber o que houve
                    erro_detalhado = payment.get("message", "Erro na API do Mercado Pago")
                    pedido.delete() 
                    return JsonResponse({'sucesso': False, 'erro': f"Mercado Pago recusou: {erro_detalhado}"})

            # ==========================================
            # ALARME NATIVO NO CELULAR (NTFY)
            # ==========================================
            topico_secreto = "duporto_pedidos_vip_2026" 
            msg_alerta = (
                f"🚨 ALERTA DE VENDA 🚨\n"
                f"👤 Cliente: {lead.nome_restaurante}\n"
                f"💰 Valor: R$ {total_calculado:.2f}\n"
                f"💳 Pagamento: {forma_pagamento}\n"
                f"📍 Endereço: {endereco}"
            )
            
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"https://ntfy.sh/{topico_secreto}", 
                    data=msg_alerta.encode('utf-8'), 
                    method="POST"
                )
                req.add_header("Title", f"Novo Pedido: #{pedido.id}") 
                req.add_header("Tags", "fish,moneybag") 
                urllib.request.urlopen(req)
            except Exception as e:
                print(f"Falha ao enviar Ntfy: {e}")

            # --- WHATSAPP DO CLIENTE ---
            data_formatada = "Sem data" if not data_entrega else data_entrega
            hora_formatada = "Sem hora" if not hora_entrega else hora_entrega
            texto_wpp = f"Fala Peixaria Duporto! Confirmei o *Pedido #{pedido.id}*.\n\n📍 *Entrega:* {endereco}\n📅 *Data:* {data_formatada} às {hora_formatada}\n💰 *Total:* R$ {total_calculado:.2f}"
            link_whatsapp_oficial = f"https://wa.me/5551996799655?text={quote(texto_wpp)}"

            return JsonResponse({
                'sucesso': True, 
                'pedido_id': pedido.id, 
                'total': float(total_calculado),
                'forma_pagamento': forma_pagamento, 
                'link_whatsapp': link_whatsapp_oficial,
                'qr_code_64': qr_code_base64, 
                'pix_copia_cola': pix_copia_cola
            })
        except Exception as e: 
            return JsonResponse({'sucesso': False, 'erro': str(e)})
    return JsonResponse({'sucesso': False})

# ==========================================
# WEBHOOK MERCADO PAGO (AUTOMAÇÃO DE PAGAMENTO)
# ==========================================
@csrf_exempt
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            # O Mercado Pago avisa que algo aconteceu
            dados = json.loads(request.body)
            acao = dados.get('action') or dados.get('type')
            
            if acao == 'payment.created' or acao == 'payment':
                # Pega o ID do pagamento lá no Mercado Pago
                pagamento_id = dados.get('data', {}).get('id')
                
                if pagamento_id:
                    # Vai no Mercado Pago e pergunta: "Esse pagamento foi aprovado mesmo?"
                    resposta = sdk.payment().get(pagamento_id)
                    info = resposta.get("response", {})
                    
                    if info.get('status') == 'approved':
                        # Pega o crachá do pedido que mandamos antes
                        pedido_id = info.get('external_reference')
                        
                        if pedido_id:
                            # Marca como PAGO no nosso banco de dados automaticamente!
                            pedido = Pedido.objects.get(id=pedido_id)
                            pedido.status = 'PAGO'
                            pedido.save()
                            
        except Exception as e:
            print(f"Erro no Webhook: {e}")
            
    # O Mercado Pago EXIGE que a gente responda "200 OK" rápido, senão ele fica mandando de novo
    return HttpResponse(status=200)


# ==========================================
# SUPER ADMIN: MODO DEUS (RELATÓRIOS E EXCLUSÕES BRUTAS)
# ==========================================
@login_required
def admin_customizado(request):
    leads = LeadRestaurante.objects.all().order_by('-id')
    pedidos = Pedido.objects.all().order_by('-id')
    return render(request, 'admin_customizado.html', {'leads': leads, 'pedidos': pedidos})

@login_required
def deletar_lead(request, lead_id):
    lead = LeadRestaurante.objects.get(id=lead_id)
    lead.delete()
    return redirect('admin_customizado')

@login_required
def deletar_pedido(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    pedido.delete()
    return redirect('admin_customizado')

@login_required
def exportar_leads(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="base_clientes_banca5.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Nome do Restaurante', 'CNPJ', 'WhatsApp', 'Data de Cadastro', 'Link VIP'])
    
    leads = LeadRestaurante.objects.all()
    for lead in leads:
        writer.writerow([lead.id, lead.nome_restaurante, lead.cnpj, lead.whatsapp, localtime(lead.data_cadastro).strftime("%d/%m/%Y"), f"http://{request.get_host()}/catalogo/{lead.token_acesso}/"])
    
    return response

@login_required
def exportar_vendas(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorio_vendas_banca5.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID Pedido', 'Data', 'Restaurante', 'CNPJ', 'Valor Total (R$)', 'Forma Pagamento', 'Status'])
    
    pedidos = Pedido.objects.all()
    for pedido in pedidos:
        writer.writerow([pedido.id, localtime(pedido.data_pedido).strftime("%d/%m/%Y %H:%M"), pedido.lead.nome_restaurante, pedido.lead.cnpj, str(pedido.valor_total).replace('.', ','), pedido.forma_pagamento, pedido.status])
    
    return response