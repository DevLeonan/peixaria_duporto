from django.contrib import admin
from django.urls import path
from funil_vendas import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ÁREA DO CLIENTE ---
    # Tela Inicial (Captura de Leads)
    path('', views.pagina_captura, name='captura'),
    
    # Catálogo B2B com Link Mágico
    path('catalogo/<uuid:token>/', views.catalogo_precos, name='catalogo_precos'),
    
    # Rota invisível que salva o pedido e gera o QR Code no catálogo
    path('catalogo/<uuid:token>/finalizar/', views.finalizar_pedido, name='finalizar_pedido'),
    
    
    # --- ÁREA DO DONO (SISTEMA INTERNO) ---
    # Centro de Comando (Dashboard Financeiro)
    path('painel/', views.painel_interno, name='painel_interno'),
    
    # Gestão de Estoque (Adicionar/Listar Peixes)
    path('painel/produtos/', views.gerenciar_produtos, name='gerenciar_produtos'),
    
    # --- NOVAS ROTAS: EDIÇÃO E CONTROLE DE ESTOQUE ---
    path('painel/produtos/<int:produto_id>/editar/', views.editar_produto, name='editar_produto'),
    path('painel/produtos/<int:produto_id>/toggle/', views.toggle_produto, name='toggle_produto'), # Pausar/Ativar
    path('painel/produtos/<int:produto_id>/excluir/', views.excluir_produto, name='excluir_produto'),
    
    # Rota invisível para o botão "Confirmar Pagamento" do Dashboard
    path('painel/pedido/<int:pedido_id>/status/', views.atualizar_status_pedido, name='atualizar_status_pedido'),
    
    # --- NOVAS ROTAS DE ESCALA E SEGURANÇA ---
    # Rota invisível onde o celular vai checar se chegou pedido (Notificação Push)
    path('painel/api/checar-pedidos/', views.checar_novos_pedidos, name='checar_novos_pedidos'),
    
    # Rota invisível para zerar o caixa (Limpeza)
    path('painel/api/limpar-caixa/', views.limpar_dados_caixa, name='limpar_dados_caixa'),

    # ==========================================
    # SUPER ADMIN CUSTOMIZADO (MODO DEUS)
    # ==========================================
    # Rota para acessar a tela
    path('painel/deus/', views.admin_customizado, name='admin_customizado'),
    
    # Rotas de Exportação de Excel (CSV)
    path('painel/deus/exportar-leads/', views.exportar_leads, name='exportar_leads'),
    path('painel/deus/exportar-vendas/', views.exportar_vendas, name='exportar_vendas'),
    
    # Rotas de Destruição (Apagar do Banco)
    path('painel/deus/lead/<int:lead_id>/deletar/', views.deletar_lead, name='deletar_lead'),
    path('painel/deus/pedido/<int:pedido_id>/deletar/', views.deletar_pedido, name='deletar_pedido'),
    # ==========================================
    # WEBHOOK MERCADO PAGO (O OLHEIRO)
    # ==========================================
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
]
]