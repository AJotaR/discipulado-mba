import json
import os
import re
import streamlit as st
from PIL import Image
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Discipulado MBA SEDE", page_icon="📖", layout="wide"
)

# --- CONFIGURAÇÃO DE SEGURANÇA ---
SENHA_ADMIN = st.secrets.get("SENHA_ADMIN", "admin123")

# --- CONEXÃO COM O SUPABASE ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro ao conectar ao Supabase: {e}")

CARGOS_DISPONIVEIS = [
    "Apóstola",
    "Apóstolo",
    "Bispa",
    "Bispo",
    "Cooperador",
    "Cooperadora",
    "Diaconisa",
    "Diácono",
    "Evangelista",
    "Membro",
    "Missionária",
    "Missionário",
    "Obreira",
    "Obreiro",
    "Pastora",
    "Pastor",
    "Presbítera",
    "Presbítero",
]

DIAS_SEMANA_ORDEM = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]

MODULOS_MESES = [
    {
        "tag": "JUN",
        "titulo": "PROPÓSITO ETERNO DE DEUS",
        "pasta": "junho",
        "chave": "junho",
    },
    {
        "tag": "JUL",
        "titulo": "JESUS, SUA VIDA E SUA OBRA",
        "pasta": "julho",
        "chave": "julho",
    },
    {
        "tag": "AGO",
        "titulo": "PREGAÇÃO DE JESUS E DOS APÓSTOLOS",
        "pasta": "agosto",
        "chave": "agosto",
    },
    {
        "tag": "SET",
        "titulo": "O QUE SIGNIFICA O EVANGELHO DO REINO",
        "pasta": "setembro",
        "chave": "setembro",
    },
    {
        "tag": "OUT",
        "titulo": "O EVANGELHO DO REINO X O EVANGELHO DAS OFERTAS",
        "pasta": "outubro",
        "chave": "outubro",
    },
    {
        "tag": "NOV",
        "titulo": "O DISCÍPULO E O RELIGIOSO",
        "pasta": "novembro",
        "chave": "novembro",
    },
    {
        "tag": "DEZ",
        "titulo": "TRABALHANDO A MULTIPLICAÇÃO ATRAVÉS DO ENVIO",
        "pasta": "dezembro",
        "chave": "dezembro",
    },
]

# --- FUNÇÃO AUXILIAR PARA EXIBIR VÍDEOS DO YOUTUBE ---
def exibir_video_youtube(url):
    """Converte qualquer link do YouTube (live, shorts, watch, youtu.be) para embed seguro"""
    video_id = None
    if "youtube.com/live/" in url:
        video_id = url.split("youtube.com/live/")[1].split("?")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    elif "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "shorts/" in url:
        video_id = url.split("shorts/")[1].split("?")[0]

    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        st.iframe(embed_url, height=450)
    else:
        st.video(url)

# --- PERSISTÊNCIA DE DADOS (SUPABASE) ---
def carregar_dados():
    if supabase:
        try:
            res = (
                supabase.table("dados_app")
                .select("conteudo")
                .eq("id", 1)
                .execute()
            )
            if res.data:
                dados = res.data[0]["conteudo"]
                dados.setdefault("leitura", {})
                dados.setdefault("oracao", {})
                dados.setdefault("jejum", {})
                dados.setdefault("discipuladores", [])
                dados.setdefault("mapas", {})
                dados.setdefault("videos", {})
                dados.setdefault("pendentes_oracao", {})
                dados.setdefault("pendentes_jejum", {})
                dados.setdefault("galeria_fotos", [])
                dados.setdefault("comentarios_galeria", [])
                
                for disc in dados["discipuladores"]:
                    if "dia" not in disc or disc["dia"] not in DIAS_SEMANA_ORDEM:
                        disc["dia"] = "Segunda-feira"
                        
                return dados
        except Exception:
            pass
    return {
        "leitura": {},
        "oracao": {},
        "jejum": {},
        "discipuladores": [],
        "mapas": {},
        "videos": {},
        "pendentes_oracao": {},
        "pendentes_jejum": {},
        "galeria_fotos": [],
        "comentarios_galeria": [],
    }

def salvar_dados(dados):
    if supabase:
        try:
            res = (
                supabase.table("dados_app")
                .select("id")
                .eq("id", 1)
                .execute()
            )
            if res.data:
                supabase.table("dados_app").update({"conteudo": dados}).eq(
                    "id", 1
                ).execute()
            else:
                supabase.table("dados_app").insert(
                    {"id": 1, "conteudo": dados}
                ).execute()
        except Exception as e:
            st.error(f"Erro ao salvar dados no Supabase: {e}")

# --- FUNÇÃO DE UPLOAD DE IMAGEM ---
def upload_imagem(file, caminho_destino):
    if supabase:
        caminho_limpo = re.sub(r"[^a-zA-Z0-9_./-]", "_", caminho_destino)
        bytes_data = file.getbuffer().tobytes()

        for bucket_nome in ["MIDIAS", "midias"]:
            try:
                supabase.storage.from_(bucket_nome).upload(
                    caminho_limpo,
                    bytes_data,
                    file_options={"upsert": "true"},
                )
                return supabase.storage.from_(bucket_nome).get_public_url(caminho_limpo)
            except Exception as e:
                err_msg = str(e)
                if "Bucket not found" in err_msg or "404" in err_msg:
                    try:
                        supabase.storage.create_bucket(bucket_nome, options={"public": True})
                        supabase.storage.from_(bucket_nome).upload(
                            caminho_limpo,
                            bytes_data,
                            file_options={"upsert": "true"},
                        )
                        return supabase.storage.from_(bucket_nome).get_public_url(caminho_limpo)
                    except Exception:
                        continue
                else:
                    st.error(f"Erro no envio da imagem: {e}")
                    return ""

        st.error("Não foi possível salvar no Storage. Verifique as permissões do Supabase.")
    return ""

dados = carregar_dados()

# --- ESTADO DE SESSÃO ---
if "es_admin" not in st.session_state:
    st.session_state.es_admin = False
if "mostrar_campo_senha" not in st.session_state:
    st.session_state.mostrar_campo_senha = False
if "palavras_encontradas" not in st.session_state:
    st.session_state.palavras_encontradas = []

# --- CONTAGEM DE SOLICITAÇÕES PENDENTES ---
total_pendentes_oracao = sum(len(v) for v in dados.get("pendentes_oracao", {}).values())
total_pendentes_jejum = sum(len(v) for v in dados.get("pendentes_jejum", {}).values())
total_geral_pendentes = total_pendentes_oracao + total_pendentes_jejum

# --- BARRA LATERAL (MENU & ÁREA DO ADMIN) ---
st.sidebar.title("📖 Discipulado MBA")

opcoes_menu = [
    "📚 Temas & Mapas",
    "🎬 Vídeos & Aulas",
    "📖 Leitura Bíblica",
    "⏰ Relógio de Oração",
    "🗓️ Calendário de Jejum",
    "👥 Discipuladores",
    "📸 Galeria & Depoimentos",
    "🎮 Jogos Bíblicos",
]

if st.session_state.es_admin:
    rotulo_notificacao = (
        f"🔔 Solicitações ({total_geral_pendentes} pendentes)"
        if total_geral_pendentes > 0
        else "🔔 Solicitações"
    )
    opcoes_menu.append(rotulo_notificacao)

pagina = st.sidebar.radio("Navegação", opcoes_menu)

st.sidebar.divider()

if not st.session_state.es_admin:
    if st.sidebar.button("🔐 Área do Administrador"):
        st.session_state.mostrar_campo_senha = not st.session_state.mostrar_campo_senha

    if st.session_state.mostrar_campo_senha:
        senha_digitada = st.sidebar.text_input("Digite a senha master:", type="password")
        if st.sidebar.button("Entrar"):
            if senha_digitada == SENHA_ADMIN:
                st.session_state.es_admin = True
                st.session_state.mostrar_campo_senha = False
                st.sidebar.success("Modo Admin Ativado!")
                st.rerun()
            else:
                st.sidebar.error("Senha incorreta!")
else:
    st.sidebar.success("🔓 Você está no modo Administrador")
    if st.sidebar.button("🚪 Sair do modo Admin"):
        st.session_state.es_admin = False
        st.rerun()

st.sidebar.divider()
logo_path = "logo.png"
if os.path.exists(logo_path):
    col_v1, col_logo, col_v2 = st.sidebar.columns([1, 3, 1])
    with col_logo:
        st.image(logo_path, width=180)

es_admin = st.session_state.es_admin

# --- TELA 1: TEMAS & MAPAS MENTAIS ---
if pagina == "📚 Temas & Mapas":
    st.title("📚 Temas & Mapas Mentais")
    st.caption("O EVANGELHO DO REINO")

    dados.setdefault("mapas", {})
    dados.setdefault("videos", {})

    for mod in MODULOS_MESES:
        chave_mes = mod["chave"]
        dados["mapas"].setdefault(chave_mes, [])
        dados["videos"].setdefault(chave_mes, [])

        with st.expander(f"📌 {mod['tag']} - {mod['titulo']}"):
            st.markdown("#### 🗺️ Mapas Mentais")
            if es_admin:
                mapa_upload = st.file_uploader(
                    f"Adicionar Mapa para {mod['tag']}",
                    type=["png", "jpg", "jpeg"],
                    key=f"up_{chave_mes}",
                )
                if mapa_upload:
                    caminho_remote = f"mapas/{chave_mes}_{mapa_upload.name}"
                    url = upload_imagem(mapa_upload, caminho_remote)
                    if url:
                        dados["mapas"][chave_mes].append(url)
                        salvar_dados(dados)
                        st.success("Mapa adicionado com sucesso!")
                        st.rerun()

            imagens = dados["mapas"].get(chave_mes, [])
            if imagens:
                for idx_img, img_url in enumerate(imagens):
                    st.image(img_url, width="stretch")
                    if es_admin:
                        if st.button("🗑️ Excluir esta imagem", key=f"del_img_{chave_mes}_{idx_img}"):
                            dados["mapas"][chave_mes].pop(idx_img)
                            salvar_dados(dados)
                            st.rerun()
            else:
                st.info("Nenhum mapa mental cadastrado para este mês.")

            st.divider()

            st.markdown("#### 🎬 Vídeos & Aulas do YouTube")
            if es_admin:
                col_url, col_btn = st.columns([3, 1])
                url_video = col_url.text_input(
                    "Cole o Link do YouTube (ex: https://youtube.com/live/...)",
                    key=f"url_v_{chave_mes}",
                )
                if col_btn.button("➕ Adicionar Vídeo", key=f"btn_v_{chave_mes}"):
                    if url_video:
                        dados["videos"][chave_mes].append(url_video)
                        salvar_dados(dados)
                        st.success("Vídeo adicionado com sucesso!")
                        st.rerun()

            lista_videos = dados["videos"].get(chave_mes, [])
            if lista_videos:
                for idx_v, video_url in enumerate(lista_videos):
                    exibir_video_youtube(video_url)
                    if es_admin:
                        if st.button("🗑️ Excluir este vídeo", key=f"del_v_{chave_mes}_{idx_v}"):
                            dados["videos"][chave_mes].pop(idx_v)
                            salvar_dados(dados)
                            st.rerun()
            else:
                st.info("Nenhum vídeo cadastrado para este mês.")

# --- TELA 2: VÍDEOS & AULAS ---
elif pagina == "🎬 Vídeos & Aulas":
    st.title("🎬 Vídeos & Aulas do Discipulado")
    st.caption("Acesse diretamente todas as pregações e estudos do YouTube divididos por mês.")

    dados.setdefault("videos", {})

    for mod in MODULOS_MESES:
        chave_mes = mod["chave"]
        dados["videos"].setdefault(chave_mes, [])

        with st.expander(f"🎥 {mod['tag']} - {mod['titulo']}"):
            if es_admin:
                col_url, col_btn = st.columns([3, 1])
                url_video = col_url.text_input(
                    "Cole o Link do YouTube", key=f"url_v_at_{chave_mes}"
                )
                if col_btn.button("➕ Adicionar Vídeo", key=f"btn_v_at_{chave_mes}"):
                    if url_video:
                        dados["videos"][chave_mes].append(url_video)
                        salvar_dados(dados)
                        st.success("Vídeo adicionado com sucesso!")
                        st.rerun()

            lista_videos = dados["videos"].get(chave_mes, [])
            if lista_videos:
                for idx_v, video_url in enumerate(lista_videos):
                    exibir_video_youtube(video_url)
                    if es_admin:
                        if st.button("🗑️ Excluir este vídeo", key=f"del_v_at_{chave_mes}_{idx_v}"):
                            dados["videos"][chave_mes].pop(idx_v)
                            salvar_dados(dados)
                            st.rerun()
            else:
                st.info("Nenhum vídeo cadastrado para este mês.")

# --- TELA 3: LEITURA BÍBLICA ---
elif pagina == "📖 Leitura Bíblica":
    st.title("📖 Plano de Leitura Bíblica Mensal")

    mes_sel = st.selectbox(
        "Selecione o Mês",
        [m["chave"] for m in MODULOS_MESES],
        format_func=lambda x: x.capitalize(),
    )

    if mes_sel not in dados["leitura"]:
        dados["leitura"][mes_sel] = []

    if es_admin:
        col1, col2 = st.columns([3, 1])
        nova_leitura = col1.text_input("Nova leitura (Ex: Dia 01: Mateus 1-4)")
        if col2.button("➕ Adicionar Leitura") and nova_leitura:
            dados["leitura"][mes_sel].append({"texto": nova_leitura, "concluido": False})
            salvar_dados(dados)
            st.rerun()

    st.divider()

    for i, item in enumerate(dados["leitura"][mes_sel]):
        col_chk, col_del = st.columns([4, 1])
        status = col_chk.checkbox(
            item["texto"], value=item.get("concluido", False), key=f"chk_{mes_sel}_{i}"
        )
        if status != item.get("concluido", False):
            dados["leitura"][mes_sel][i]["concluido"] = status
            salvar_dados(dados)

        if es_admin:
            if col_del.button("❌", key=f"del_leit_{mes_sel}_{i}"):
                dados["leitura"][mes_sel].pop(i)
                salvar_dados(dados)
                st.rerun()

# --- TELA 4: RELÓGIO DE ORAÇÃO ---
elif pagina == "⏰ Relógio de Oração":
    st.title("⏰ Relógio de Oração (Escala 30m)")

    dados.setdefault("pendentes_oracao", {})

    horas = [
        f"{h:02d}:{m:02d} - {(h if m==0 else h+1)%24:02d}:{(m+30)%60:02d}"
        for h in range(24)
        for m in (0, 30)
    ]
    turno_sel = st.selectbox("Selecione o Turno de Oração", horas)

    if turno_sel not in dados["oracao"]:
        dados["oracao"][turno_sel] = []
    if turno_sel not in dados["pendentes_oracao"]:
        dados["pendentes_oracao"][turno_sel] = []

    with st.expander("📝 Cadastro para este horário de oração", expanded=True):
        if es_admin:
            with st.form(f"form_oracao_admin_{turno_sel}"):
                c1, c2 = st.columns(2)
                cargo = c1.selectbox("Cargo", CARGOS_DISPONIVEIS)
                nome = c2.text_input("Nome do Intercessor")
                if st.form_submit_button("➕ Publicar Direto (Admin)") and nome:
                    dados["oracao"][turno_sel].append({"cargo": cargo, "nome": nome})
                    salvar_dados(dados)
                    st.success("Intercessor adicionado à escala!")
                    st.rerun()
        else:
            with st.form(f"form_oracao_user_{turno_sel}"):
                c1, c2 = st.columns(2)
                cargo = c1.selectbox("Seu Cargo:", CARGOS_DISPONIVEIS)
                nome = c2.text_input("Seu Nome Completo:")
                if st.form_submit_button("📩 Enviar Cadastro") and nome:
                    novo_cad = {"cargo": cargo, "nome": nome}
                    dados["pendentes_oracao"][turno_sel].append(novo_cad)
                    salvar_dados(dados)
                    st.info("⏳ Cadastro enviado com sucesso! Aguardando a aprovação do administrador.")
                    st.rerun()

    if not es_admin and dados["pendentes_oracao"][turno_sel]:
        st.caption("Seus cadastros pendentes neste horário:")
        for idx_p, item_p in enumerate(list(dados["pendentes_oracao"][turno_sel])):
            col_info, col_edt, col_del = st.columns([3, 1, 1])
            col_info.write(f"⏳ **[{item_p['cargo']}]** {item_p['nome']} *(Aguardando aprovação)*")

            with col_edt.popover("✏️ Editar"):
                with st.form(f"form_edit_or_p_{turno_sel}_{idx_p}"):
                    index_cargo = (
                        CARGOS_DISPONIVEIS.index(item_p["cargo"])
                        if item_p["cargo"] in CARGOS_DISPONIVEIS
                        else 0
                    )
                    nc = st.selectbox("Novo Cargo", CARGOS_DISPONIVEIS, index=index_cargo)
                    nn = st.text_input("Novo Nome", value=item_p["nome"])
                    if st.form_submit_button("Salvar") and nn:
                        dados["pendentes_oracao"][turno_sel][idx_p] = {"cargo": nc, "nome": nn}
                        salvar_dados(dados)
                        st.rerun()

            if col_del.button("🗑️", key=f"del_user_or_p_{turno_sel}_{idx_p}"):
                dados["pendentes_oracao"][turno_sel].pop(idx_p)
                salvar_dados(dados)
                st.rerun()

    st.subheader(f"Intercessores confirmados para {turno_sel}:")
    if dados["oracao"][turno_sel]:
        for i, item in enumerate(dados["oracao"][turno_sel]):
            c_txt, c_del = st.columns([4, 1])
            cargo_str = f"[{item['cargo']}] " if item.get("cargo") else ""
            c_txt.write(f"🙏 **{cargo_str}**{item['nome']}")
            if es_admin and c_del.button("❌", key=f"del_or_{turno_sel}_{i}"):
                dados["oracao"][turno_sel].pop(i)
                salvar_dados(dados)
                st.rerun()
    else:
        st.info("Nenhum intercessor confirmado neste horário ainda.")

# --- TELA 5: CALENDÁRIO DE JEJUM ---
elif pagina == "🗓️ Calendário de Jejum":
    st.title("🗓️ Calendário Semanal de Jejum")

    dados.setdefault("pendentes_jejum", {})

    dia_sel = st.selectbox("Selecione o Dia da Semana", DIAS_SEMANA_ORDEM)

    if dia_sel not in dados["jejum"]:
        dados["jejum"][dia_sel] = []
    if dia_sel not in dados["pendentes_jejum"]:
        dados["pendentes_jejum"][dia_sel] = []

    with st.expander(f"📝 Cadastro para jejuar na {dia_sel}", expanded=True):
        if es_admin:
            with st.form(f"form_jejum_admin_{dia_sel}"):
                c1, c2 = st.columns(2)
                cargo = c1.selectbox("Cargo", CARGOS_DISPONIVEIS)
                nome = c2.text_input("Nome da Pessoa")
                if st.form_submit_button("➕ Publicar Direto (Admin)") and nome:
                    dados["jejum"][dia_sel].append({"cargo": cargo, "nome": nome})
                    salvar_dados(dados)
                    st.success("Pessoa adicionada ao jejum!")
                    st.rerun()
        else:
            with st.form(f"form_jejum_user_{dia_sel}"):
                c1, c2 = st.columns(2)
                cargo = c1.selectbox("Seu Cargo:", CARGOS_DISPONIVEIS)
                nome = c2.text_input("Seu Nome Completo:")
                if st.form_submit_button("📩 Enviar Cadastro") and nome:
                    novo_cad = {"cargo": cargo, "nome": nome}
                    dados["pendentes_jejum"][dia_sel].append(novo_cad)
                    salvar_dados(dados)
                    st.info("⏳ Cadastro enviado com sucesso! Aguardando a aprovação do administrador.")
                    st.rerun()

    if not es_admin and dados["pendentes_jejum"][dia_sel]:
        st.caption("Seus cadastros pendentes neste dia:")
        for idx_p, item_p in enumerate(list(dados["pendentes_jejum"][dia_sel])):
            col_info, col_edt, col_del = st.columns([3, 1, 1])
            col_info.write(f"⏳ **[{item_p['cargo']}]** {item_p['nome']} *(Aguardando aprovação)*")

            with col_edt.popover("✏️ Editar"):
                with st.form(f"form_edit_j_p_{dia_sel}_{idx_p}"):
                    index_cargo = (
                        CARGOS_DISPONIVEIS.index(item_p["cargo"])
                        if item_p["cargo"] in CARGOS_DISPONIVEIS
                        else 0
                    )
                    nc = st.selectbox("Novo Cargo", CARGOS_DISPONIVEIS, index=index_cargo)
                    nn = st.text_input("Novo Nome", value=item_p["nome"])
                    if st.form_submit_button("Salvar") and nn:
                        dados["pendentes_jejum"][dia_sel][idx_p] = {"cargo": nc, "nome": nn}
                        salvar_dados(dados)
                        st.rerun()

            if col_del.button("🗑️", key=f"del_user_j_p_{dia_sel}_{idx_p}"):
                dados["pendentes_jejum"][dia_sel].pop(idx_p)
                salvar_dados(dados)
                st.rerun()

    st.subheader(f"Escala de Jejum confirmada - {dia_sel}:")
    if dados["jejum"][dia_sel]:
        for i, item in enumerate(dados["jejum"][dia_sel]):
            c_txt, c_del = st.columns([4, 1])
            cargo_txt = f"[{item['cargo']}] " if item.get("cargo") else ""
            c_txt.write(f"🍞 **{cargo_txt}**{item['nome']}")
            if es_admin and c_del.button("❌", key=f"del_j_{dia_sel}_{i}"):
                dados["jejum"][dia_sel].pop(i)
                salvar_dados(dados)
                st.rerun()
    else:
        st.info("Nenhuma pessoa confirmada no jejum para este dia ainda.")

# --- TELA 6: DISCIPULADORES ---
elif pagina == "👥 Discipuladores":
    st.title("👥 Encontro dos Discipuladores")
    st.caption("Organizados de acordo com o dia da semana. Clique no botão para entrar no grupo de WhatsApp!")

    if es_admin:
        with st.expander("➕ Cadastrar Novo Discipulador", expanded=True):
            with st.form("form_discipulador"):
                c1, c2 = st.columns(2)
                cargo = c1.selectbox("Cargo", CARGOS_DISPONIVEIS)
                nome = c2.text_input("Nome do Discipulador(a)")
                dia = c1.selectbox("Dia do Encontro", DIAS_SEMANA_ORDEM)
                horario = c2.text_input("Horário (ex: 19:30)")
                link_whatsapp = st.text_input("Link do Grupo do WhatsApp (ex: https://chat.whatsapp.com/...)")
                foto_file = st.file_uploader("Foto do Discipulador", type=["png", "jpg", "jpeg"])

                if st.form_submit_button("Salvar Discipulador") and nome:
                    url_foto = ""
                    if foto_file:
                        extensao = foto_file.name.split(".")[-1]
                        caminho_foto = f"discipuladores/{nome}.{extensao}"
                        url_foto = upload_imagem(foto_file, caminho_foto)

                    dados["discipuladores"].append(
                        {
                            "cargo": cargo,
                            "nome": nome,
                            "dia": dia,
                            "horario": horario,
                            "whatsapp": link_whatsapp,
                            "foto": url_foto,
                            "participantes": [],
                        }
                    )
                    salvar_dados(dados)
                    st.success("Discipulador cadastrado com sucesso!")
                    st.rerun()

    st.divider()

    todos_discipuladores = dados.get("discipuladores", [])

    if not todos_discipuladores:
        st.info("Nenhum discipulador cadastrado até o momento.")
    else:
        for dia in DIAS_SEMANA_ORDEM:
            discipuladores_do_dia = [
                (idx, d) for idx, d in enumerate(todos_discipuladores)
                if d.get("dia", "Segunda-feira") == dia
            ]

            if discipuladores_do_dia:
                st.subheader(f"📅 {dia}")

                for idx, disc in discipuladores_do_dia:
                    disc.setdefault("participantes", [])
                    disc.setdefault("whatsapp", "")

                    with st.container():
                        col_img, col_info, col_p = st.columns([1.5, 2.5, 2])

                        if disc.get("foto"):
                            col_img.image(disc["foto"], width=150)
                        else:
                            col_img.write("👤 *Sem Foto*")

                        col_info.subheader(f"{disc.get('cargo', '')} {disc['nome']}")
                        col_info.write(f"⏰ **Horário:** {disc.get('horario', 'A combinar')}")
                        col_info.write(f"👥 **Participantes:** {len(disc['participantes'])}")

                        link_wa = disc.get("whatsapp", "").strip()
                        if link_wa:
                            col_info.markdown(
                                f"""
                                <a href="{link_wa}" target="_blank" style="text-decoration: none;">
                                    <div style="
                                        background-color: #25D366;
                                        color: white;
                                        padding: 8px 14px;
                                        border-radius: 8px;
                                        font-weight: bold;
                                        text-align: center;
                                        display: inline-block;
                                        margin-top: 5px;
                                        box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
                                    ">
                                        💬 Quero Fazer Parte (WhatsApp)
                                    </div>
                                </a>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            col_info.caption("⚠️ *Link do WhatsApp não cadastrado*")

                        if es_admin:
                            c_btn1, c_btn2 = col_info.columns(2)

                            if c_btn1.button("🗑️ Remover", key=f"del_disc_{idx}"):
                                dados["discipuladores"].pop(idx)
                                salvar_dados(dados)
                                st.rerun()

                            with col_info.expander("✏️ Editar Discipulador"):
                                with st.form(f"form_edit_disc_{idx}"):
                                    index_cargo = (
                                        CARGOS_DISPONIVEIS.index(disc.get("cargo"))
                                        if disc.get("cargo") in CARGOS_DISPONIVEIS
                                        else 0
                                    )
                                    index_dia = (
                                        DIAS_SEMANA_ORDEM.index(disc.get("dia", "Segunda-feira"))
                                        if disc.get("dia", "Segunda-feira") in DIAS_SEMANA_ORDEM
                                        else 0
                                    )
                                    e_cargo = st.selectbox(
                                        "Cargo", CARGOS_DISPONIVEIS, index=index_cargo, key=f"ecargo_{idx}"
                                    )
                                    e_nome = st.text_input("Nome", value=disc.get("nome", ""), key=f"enome_{idx}")
                                    e_dia = st.selectbox("Dia", DIAS_SEMANA_ORDEM, index=index_dia, key=f"edia_{idx}")
                                    e_horario = st.text_input("Horário", value=disc.get("horario", ""), key=f"ehora_{idx}")
                                    e_whatsapp = st.text_input("Link WhatsApp", value=disc.get("whatsapp", ""), key=f"ewa_{idx}")
                                    e_foto = st.file_uploader(
                                        "Trocar Foto (Opcional)", type=["png", "jpg", "jpeg"], key=f"efoto_{idx}"
                                    )

                                    if st.form_submit_button("💾 Salvar Alterações"):
                                        disc["cargo"] = e_cargo
                                        disc["nome"] = e_nome
                                        disc["dia"] = e_dia
                                        disc["horario"] = e_horario
                                        disc["whatsapp"] = e_whatsapp

                                        if e_foto:
                                            extensao = e_foto.name.split(".")[-1]
                                            caminho_foto = f"discipuladores/{e_nome}.{extensao}"
                                            url_nova = upload_imagem(e_foto, caminho_foto)
                                            if url_nova:
                                                disc["foto"] = url_nova

                                        salvar_dados(dados)
                                        st.success("Discipulador atualizado com sucesso!")
                                        st.rerun()

                        with col_p.expander(f"👥 Ver Participantes ({len(disc['participantes'])})"):
                            for p_idx, part in enumerate(disc["participantes"]):
                                cp_txt, cp_del = st.columns([3, 1])
                                cp_txt.write(f"• [{part.get('cargo', 'Membro')}] {part['nome']}")
                                if es_admin and cp_del.button("❌", key=f"del_part_{idx}_{p_idx}"):
                                    disc["participantes"].pop(p_idx)
                                    salvar_dados(dados)
                                    st.rerun()

                            if es_admin:
                                st.caption("Adicionar Participante:")
                                p_cargo = st.selectbox("Cargo", CARGOS_DISPONIVEIS, key=f"pcargo_{idx}")
                                p_nome = st.text_input("Nome", key=f"pnome_{idx}")
                                if st.button("➕ Adicionar Membro", key=f"btn_p_{idx}") and p_nome:
                                    disc["participantes"].append({"cargo": p_cargo, "nome": p_nome})
                                    salvar_dados(dados)
                                    st.rerun()

                    st.divider()

# --- TELA 7: GALERIA DE FOTOS COM CURTIDAS E COMENTÁRIOS ---
elif pagina == "📸 Galeria & Depoimentos":
    st.title("📸 Galeria de Fotos & Depoimentos")
    st.caption("Acompanhe os momentos do discipulado, curta e deixe o seu comentário em cada foto.")

    dados.setdefault("galeria_fotos", [])

    if es_admin:
        with st.expander("➕ Adicionar Nova Foto à Galeria (Admin)"):
            with st.form("form_add_galeria"):
                titulo_f = st.text_input("Título da Foto (Ex: Encontro de Junho)")
                legenda_f = st.text_area("Legenda/Descrição")
                foto_f = st.file_uploader("Selecione a Imagem", type=["png", "jpg", "jpeg"])

                if st.form_submit_button("📤 Publicar Foto") and foto_f:
                    caminho_foto = f"galeria/{foto_f.name}"
                    url_f = upload_imagem(foto_f, caminho_foto)

                    if url_f:
                        dados["galeria_fotos"].append(
                            {
                                "titulo": titulo_f,
                                "legenda": legenda_f,
                                "url": url_f,
                                "curtidas": 0,
                                "comentarios": [],
                            }
                        )
                        salvar_dados(dados)
                        st.success("Foto publicada com sucesso na galeria!")
                        st.rerun()

    st.divider()

    fotos_lista = dados.get("galeria_fotos", [])
    if fotos_lista:
        for idx_f, f_item in enumerate(fotos_lista):
            f_item.setdefault("comentarios", [])
            f_item.setdefault("curtidas", 0)

            with st.container():
                st.image(f_item["url"], width="stretch")

                col_tit, col_like, col_del_f = st.columns([4, 1, 1])
                with col_tit:
                    if f_item.get("titulo"):
                        st.markdown(f"### {f_item['titulo']}")
                    if f_item.get("legenda"):
                        st.write(f_item["legenda"])

                if col_like.button(f"❤️ {f_item['curtidas']}", key=f"like_foto_{idx_f}"):
                    f_item["curtidas"] += 1
                    salvar_dados(dados)
                    st.rerun()

                if es_admin:
                    if col_del_f.button("🗑️ Excluir Foto", key=f"del_foto_{idx_f}"):
                        dados["galeria_fotos"].pop(idx_f)
                        salvar_dados(dados)
                        st.rerun()

                with st.expander(f"💬 Comentários desta foto ({len(f_item['comentarios'])})"):
                    with st.form(f"form_coment_foto_{idx_f}"):
                        c1, c2 = st.columns(2)
                        cargo_c = c1.selectbox("Seu Cargo:", CARGOS_DISPONIVEIS, key=f"cg_{idx_f}")
                        nome_c = c2.text_input("Seu Nome:", key=f"nm_{idx_f}")
                        msg_c = st.text_area("Seu Comentário:", key=f"msg_{idx_f}")

                        if st.form_submit_button("💬 Enviar Comentário") and nome_c and msg_c:
                            f_item["comentarios"].append(
                                {
                                    "cargo": cargo_c,
                                    "nome": nome_c,
                                    "mensagem": msg_c,
                                    "curtidas": 0,
                                    "respostas": [],
                                }
                            )
                            salvar_dados(dados)
                            st.success("Comentário publicado!")
                            st.rerun()

                    for idx_c, c_obj in enumerate(f_item["comentarios"]):
                        c_obj.setdefault("curtidas", 0)
                        c_obj.setdefault("respostas", [])

                        st.markdown(f"**[{c_obj.get('cargo', 'Membro')}] {c_obj['nome']}**")
                        st.info(f"“{c_obj['mensagem']}”")

                        c_like_c, c_resp, c_del_c = st.columns([1.5, 2, 1])

                        if c_like_c.button(f"❤️ {c_obj['curtidas']}", key=f"like_{idx_f}_{idx_c}"):
                            c_obj["curtidas"] += 1
                            salvar_dados(dados)
                            st.rerun()

                        with c_resp.popover("💬 Responder"):
                            with st.form(f"form_resp_{idx_f}_{idx_c}"):
                                r_cargo = st.selectbox("Seu Cargo", CARGOS_DISPONIVEIS, key=f"rcg_{idx_f}_{idx_c}")
                                r_nome = st.text_input("Seu Nome", key=f"rnm_{idx_f}_{idx_c}")
                                r_msg = st.text_area("Sua Resposta", key=f"rmsg_{idx_f}_{idx_c}")

                                if st.form_submit_button("Enviar Resposta") and r_nome and r_msg:
                                    c_obj["respostas"].append(
                                        {"cargo": r_cargo, "nome": r_nome, "mensagem": r_msg}
                                    )
                                    salvar_dados(dados)
                                    st.rerun()

                        if es_admin and c_del_c.button("🗑️", key=f"del_c_{idx_f}_{idx_c}"):
                            f_item["comentarios"].pop(idx_c)
                            salvar_dados(dados)
                            st.rerun()

                        if c_obj["respostas"]:
                            for idx_r, r_obj in enumerate(c_obj["respostas"]):
                                r_col1, r_col2 = st.columns([5, 1])
                                r_col1.caption(f"↳ **[{r_obj.get('cargo', 'Membro')}] {r_obj['nome']}**: {r_obj['mensagem']}")
                                if es_admin and r_col2.button("❌", key=f"del_r_{idx_f}_{idx_c}_{idx_r}"):
                                    c_obj["respostas"].pop(idx_r)
                                    salvar_dados(dados)
                                    st.rerun()

                        st.divider()

            st.markdown("---")
    else:
        st.info("Nenhuma foto publicada na galeria ainda.")

# --- TELA 8: JOGOS BÍBLICOS ---
elif pagina == "🎮 Jogos Bíblicos":
    st.title("🎮 Jogos Bíblicos & Edificação")
    st.caption("Aprenda a palavra de Deus e fortaleça seus conhecimentos do Discipulado se divertindo!")

    aba_caca, aba_cruzada = st.tabs(["🔍 Caça-Palavras (12 Palavras)", "🧩 Palavras Cruzadas"])

    # 1. CAÇA-PALAVRAS
    with aba_caca:
        st.subheader("🔍 Caça-Palavras do Discipulado")
        st.caption("Encontre as palavras na grade e digite abaixo para pontuar!")

        LISTA_12_PALAVRAS = [
            "DISCIPULADO", "JESUS", "OBEDIENCIA", "SERVICO", "AMOR", "JEJUM", 
            "ORACAO", "FE", "BIBLIA", "ESPIRITOSANTO", "DEUS", "ARVOREDO"
        ]

        col_grid, col_lista = st.columns([2.2, 1])

        with col_lista:
            st.markdown("### 📌 Palavras (12):")
            for p in LISTA_12_PALAVRAS:
                if p in st.session_state.palavras_encontradas:
                    st.markdown(f"✅ ~~**{p}**~~")
                else:
                    st.markdown(f"⚪ **{p}**")

            st.divider()
            if st.button("🔄 Reiniciar Caça-Palavras"):
                st.session_state.palavras_encontradas = []
                st.rerun()

        with col_grid:
            grid_letras_12 = [
                ["D", "I", "S", "C", "I", "P", "U", "L", "A", "D", "O", "X"],
                ["J", "E", "S", "U", "S", "A", "M", "O", "R", "F", "E", "O"],
                ["O", "B", "E", "D", "I", "E", "N", "C", "I", "A", "P", "R"],
                ["S", "E", "R", "V", "I", "C", "O", "J", "E", "J", "U", "M"],
                ["O", "R", "A", "C", "A", "O", "B", "I", "B", "L", "I", "A"],
                ["E", "S", "P", "I", "R", "I", "T", "O", "S", "A", "N", "T"],
                ["D", "E", "U", "S", "A", "R", "V", "O", "R", "E", "D", "O"],
            ]

            # Renderização de grade em CSS super leve
            grid_html = "<div style='display: grid; grid-template-columns: repeat(12, minmax(22px, 36px)); gap: 4px; font-weight: bold; margin-bottom: 20px;'>"
            for row in grid_letras_12:
                for char in row:
                    grid_html += f"<div style='background-color: #1E1E1E; color: #4CAF50; border: 1px solid #4CAF50; border-radius: 6px; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 16px;'>{char}</div>"
            grid_html += "</div>"
            st.markdown(grid_html, unsafe_allow_html=True)

            with st.form("form_caca_palavra"):
                pal_digitada = st.selectbox("Selecione ou digite a palavra encontrada:", [""] + LISTA_12_PALAVRAS)
                
                if st.form_submit_button("✅ Verificar Palavra"):
                    if pal_digitada:
                        if pal_digitada in LISTA_12_PALAVRAS:
                            if pal_digitada not in st.session_state.palavras_encontradas:
                                st.session_state.palavras_encontradas.append(pal_digitada)
                                st.success(f"🎉 Excelente! Você encontrou **{pal_digitada}**!")
                                st.rerun()
                            else:
                                st.warning("Você já marcou essa palavra!")
                        else:
                            st.error("Palavra incorreta. Procure com atenção na grade!")

    # 2. PALAVRAS CRUZADAS
    with aba_cruzada:
        st.subheader("🧩 Palavras Cruzadas do Discipulado")
        st.caption("Diagrama interativo do jogo:")

        # Layout visual estilo tabuleiro de jogo impresso
        st.markdown(
            """
            <style>
            .cruzada-grid {
                display: grid;
                grid-template-columns: repeat(13, 30px);
                gap: 2px;
                background-color: #000;
                padding: 5px;
                border-radius: 8px;
                width: fit-content;
                margin-bottom: 20px;
            }
            .cell {
                width: 30px;
                height: 30px;
                background-color: #fff;
                color: #000;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 11px;
                font-weight: bold;
                position: relative;
            }
            .black { background-color: #111; }
            .num { position: absolute; top: 1px; left: 2px; font-size: 8px; color: #d32f2f; }
            </style>

            <div class="cruzada-grid">
                <!-- Linha 1 -->
                <div class="cell"><span class="num">1</span>D</div><div class="cell">I</div><div class="cell">S</div><div class="cell">C</div><div class="cell">I</div><div class="cell">P</div><div class="cell">U</div><div class="cell">L</div><div class="cell">A</div><div class="cell">D</div><div class="cell">O</div><div class="black"></div><div class="black"></div>
                <!-- Linha 2 -->
                <div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="cell"><span class="num">2</span>J</div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div>
                <!-- Linha 3 -->
                <div class="black"></div><div class="black"></div><div class="cell"><span class="num">3</span>O</div><div class="cell">R</div><div class="cell">A</div><div class="cell">C</div><div class="cell">A</div><div class="cell">O</div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div>
                <!-- Linha 4 -->
                <div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="cell">U</div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div>
                <!-- Linha 5 -->
                <div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="cell">M</div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div>
                <!-- Linha 6 -->
                <div class="cell"><span class="num">4</span>R</div><div class="cell">E</div><div class="cell">I</div><div class="cell">N</div><div class="cell">O</div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div>
                <!-- Linha 7 -->
                <div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="black"></div><div class="cell"><span class="num">5</span>A</div><div class="cell">R</div><div class="cell">V</div><div class="cell">O</div><div class="cell">R</div><div class="cell">E</div><div class="cell">D</div><div class="cell">O</div>
                <!-- Linha 8 -->
                <div class="cell"><span class="num">6</span>E</div><div class="cell">S</div><div class="cell">P</div><div class="cell">I</div><div class="cell">R</div><div class="cell">I</div><div class="cell">T</div><div class="cell">O</div><div class="cell">S</div><div class="cell">A</div><div class="cell">N</div><div class="cell">T</div><div class="cell">O</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("form_palavras_cruzadas"):
            col_h, col_v = st.columns(2)

            with col_h:
                st.markdown("#### ➡️ Horizontais")
                rc1 = st.text_input("1. Formar seguidores e alunos fiéis de Jesus (9 letras)", key="pc_1").strip().upper()
                rc3 = st.text_input("3. Comunicação constante e íntima com Deus (6 letras)", key="pc_3").strip().upper()
                rc4 = st.text_input("4. O Evangelho pregado por Jesus é o Evangelho do... (5 letras)", key="pc_4").strip().upper()
                rc5 = st.text_input("5. Nome da nossa sede e ministério batista (8 letras)", key="pc_5").strip().upper()

            with col_v:
                st.markdown("#### ⬇️ Verticais")
                rc2 = st.text_input("2. Prática de abstenção por propósito espiritual (5 letras)", key="pc_2").strip().upper()
                rc6 = st.text_input("6. O Consolador enviado por Jesus para guiar a Igreja (13 letras)", key="pc_6").strip().upper()

            if st.form_submit_button("🏆 Conferir Todas as Respostas"):
                acertos = 0
                GABARITO = {
                    "1": ("DISCIPULADO", rc1),
                    "2": ("JEJUM", rc2),
                    "3": ("ORACAO", rc3),
                    "4": ("REINO", rc4),
                    "5": ("ARVOREDO", rc5),
                    "6": ("ESPIRITOSANTO", rc6),
                }

                st.divider()
                st.markdown("### 📊 Resultado:")

                for num, (correto, resposta) in GABARITO.items():
                    if resposta == correto:
                        st.success(f"✅ Palavra {num}: Correto! (`{correto}`)")
                        acertos += 1
                    else:
                        st.error(f"❌ Palavra {num}: Incorreto.")

                if acertos == 6:
                    st.balloons()
                    st.success("🎉 PARABÉNS! Você completou o desafio das Palavras Cruzadas!")

# --- TELA 9: NOTIFICAÇÕES E APROVAÇÕES ---
elif "Solicitações" in pagina and es_admin:
    st.title("🔔 Central de Notificações e Aprovações")
    st.caption("Gerencie os cadastros enviados pelos membros antes de serem publicados.")

    tab_oracao, tab_jejum = st.tabs(["⏰ Relógio de Oração", "🗓️ Calendário de Jejum"])

    with tab_oracao:
        st.subheader("Solicitações para o Relógio de Oração")
        tem_pendentes_oracao = False

        for turno, lista_p in list(dados.get("pendentes_oracao", {}).items()):
            if lista_p:
                tem_pendentes_oracao = True
                st.markdown(f"##### 🕒 Turno: `{turno}`")
                for idx_p, item_p in enumerate(list(lista_p)):
                    c_info, c_ok, c_rec = st.columns([3, 1, 1])
                    c_info.write(f"👤 **[{item_p['cargo']}]** {item_p['nome']}")

                    chave_limpa = turno.replace(" ", "_").replace(":", "").replace("-", "")

                    if c_ok.button("✅ Aprovar", key=f"aprov_or_cent_{chave_limpa}_{idx_p}"):
                        dados["oracao"].setdefault(turno, []).append(item_p)
                        dados["pendentes_oracao"][turno].pop(idx_p)
                        salvar_dados(dados)
                        st.success("Cadastro aprovado!")
                        st.rerun()

                    if c_rec.button("❌ Recusar", key=f"rec_or_cent_{chave_limpa}_{idx_p}"):
                        dados["pendentes_oracao"][turno].pop(idx_p)
                        salvar_dados(dados)
                        st.rerun()
                st.divider()

        if not tem_pendentes_oracao:
            st.info("Nenhuma solicitação pendente para o Relógio de Oração.")

    with tab_jejum:
        st.subheader("Solicitações para o Calendário de Jejum")
        tem_pendentes_jejum = False

        for dia, lista_p in list(dados.get("pendentes_jejum", {}).items()):
            if lista_p:
                tem_pendentes_jejum = True
                st.markdown(f"##### 📅 Dia: `{dia}`")
                for idx_p, item_p in enumerate(list(lista_p)):
                    c_info, c_ok, c_rec = st.columns([3, 1, 1])
                    c_info.write(f"👤 **[{item_p['cargo']}]** {item_p['nome']}")

                    if c_ok.button("✅ Aprovar", key=f"aprov_j_cent_{dia}_{idx_p}"):
                        dados["jejum"].setdefault(dia, []).append(item_p)
                        dados["pendentes_jejum"][dia].pop(idx_p)
                        salvar_dados(dados)
                        st.success("Cadastro aprovado!")
                        st.rerun()

                    if c_rec.button("❌ Recusar", key=f"rec_j_cent_{dia}_{idx_p}"):
                        dados["pendentes_jejum"][dia].pop(idx_p)
                        salvar_dados(dados)
                        st.rerun()
                st.divider()

        if not tem_pendentes_jejum:
            st.info("Nenhuma solicitação pendente para o Calendário de Jejum.")