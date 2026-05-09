from django.db import models
import uuid

class LeadRestaurante(models.Model):
    # === NOVO CAMPO ADICIONADO AQUI ===
    nome_restaurante = models.CharField(max_length=150, verbose_name="Nome do Restaurante", default="Não Informado")
    
    cnpj = models.CharField(max_length=20, verbose_name="CNPJ do Cliente")
    whatsapp = models.CharField(max_length=20, verbose_name="WhatsApp")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data do Cadastro")
    virou_cliente = models.BooleanField(default=False)
    
    # A LINHA QUE FALTAVA ESTÁ AQUI EMBAIXO:
    token_acesso = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = "Lead (Interessado)"
        verbose_name_plural = "Leads (Interessados)"

    def __str__(self):
        # Agora ele vai mostrar o nome do restaurante e o CNPJ
        return f"{self.nome_restaurante} ({self.cnpj})"

class CortePescado(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Filé (Ex: Salmão Premium)")
    descricao = models.CharField(max_length=200, verbose_name="Descrição curta (Ex: Sem espinhas, a vácuo)")
    preco_por_kg = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Preço por KG (R$)")
    imagem_url = models.URLField(blank=True, null=True, verbose_name="Link da Foto")
    disponivel = models.BooleanField(default=True, verbose_name="Disponível para Venda?")

    class Meta:
        verbose_name = "Corte de Pescado"
        verbose_name_plural = "Cortes de Pescado"

    def __str__(self):
        return f"{self.nome} - R$ {self.preco_por_kg}/kg"
        
# ==========================================
# NOVO: MÓDULO DE VENDAS E FECHAMENTO DE CAIXA
# ==========================================

class Pedido(models.Model):
    # Opções de pagamento para o cliente escolher
    OPCOES_PAGAMENTO = [
        ('PIX', 'Pix (Imediato)'), # <-- Ajustado para Imediato
        ('DINHEIRO', 'Dinheiro (No ato da entrega)')
    ]
    
    # NOVO: Status do Pedido para o seu Painel Financeiro
    STATUS_PEDIDO = [
        ('PENDENTE', 'Aguardando Pagamento'),
        ('PAGO', 'Pago!'),
        ('CANCELADO', 'Cancelado')
    ]

    lead = models.ForeignKey(LeadRestaurante, on_delete=models.CASCADE, verbose_name="Cliente")
    data_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora do Pedido")
    forma_pagamento = models.CharField(max_length=20, choices=OPCOES_PAGAMENTO, default='PIX', verbose_name="Forma de Pagamento")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total (R$)")
    
    # O campo que vai dizer se a grana já entrou ou não
    status = models.CharField(max_length=20, choices=STATUS_PEDIDO, default='PENDENTE', verbose_name="Status do Pagamento")

    # === NOVOS CAMPOS PARA O AGENDAMENTO DE ENTREGA ===
    endereco_entrega = models.CharField(max_length=255, verbose_name="Endereço de Entrega", blank=True, null=True)
    data_entrega = models.DateField(verbose_name="Data Agendada", blank=True, null=True)
    hora_entrega = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        # Agora o pedido também mostra o nome do restaurante
        return f"Pedido #{self.id} - {self.lead.nome_restaurante} ({self.status})"

class ItemPedido(models.Model):
    # Relaciona o item ao pedido e ao corte de peixe específico
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    corte = models.ForeignKey(CortePescado, on_delete=models.PROTECT, verbose_name="Corte Vendido")
    quantidade_kg = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Quantidade (KG)")
    # Salva o preço da época, para que se você mudar o preço amanhã, o histórico antigo não mude
    preco_na_epoca = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Preço Pago na Época")

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    def __str__(self):
        return f"{self.quantidade_kg}kg de {self.corte.nome}"