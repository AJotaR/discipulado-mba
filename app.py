import json
import os
import streamlit as st
from PIL import Image
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Discipulado MBA SEDE", page_icon="📖", layout="wide"
)

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
                return dados
        except Exception:
            pass
    return {
        "leitura": {},
        "oracao": {},
        "jejum": {},
        "discipuladores": [],
        "mapas": {},
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


# --- FUNÇÃO DE UPLOAD AJUSTADA PARA O BUCKET 'MIDIAS' (MAIÚSCULO) ---
def upload_imagem(file, caminho_destino):
    if supabase:
        try:
            bytes_data = file.getbuffer().tobytes()
            # Nome do bucket alterado para MIDIAS
            supabase.storage.from_("MIDIAS").upload(
                caminho_destino, bytes_data, file_options={"upsert": "true"}
            )
            url = supabase.storage.from_("MIDIAS").get_public_url(
                caminho_destino
            )
            return url
        except Exception as e:
            st.error(f"Erro no envio da imagem: {e}")
            return ""
    return ""


dados = carregar_dados()

# --- ESTADO DE SESSÃO DA AUTENTICAÇÃO ---
if "es_admin" not in st.session_state:
    st.session_state.es_admin = False

if "mostrar_campo_senha" not in st.session_state:
    st.session_state.mostrar_campo_senha = False

# --- BARRA LATERAL (MENU & ÁREA DO ADMIN) ---
st.sidebar.title("📖 Discipulado MBA")

pagina = st.sidebar.radio(
    "Navegação",
    [
        "📚 Temas & Mapas",
        "📖 Leitura Bíblica",
        "⏰ Relógio de Oração",
        "🗓️ Calendário de Jejum",
        "👥 Discipuladores",
    ],
)

st.sidebar.divider()

if not st.session_state.es_admin:
    if st.sidebar.button("🔐 Área do Administrador"):
        st.session_state.mostrar_campo_senha = (
            not st.session_state.mostrar_campo_senha
        )

    if st.session_state.mostrar_campo_senha:
        senha_digitada = st.sidebar.text_input(
            "Digite a senha master:", type="password"
        )
        if st.sidebar.button("Entrar"):
            if senha_digitada == "admin123":
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

es_admin = st.session_state.es_admin

# --- TELA 1: TEMAS E MAPAS MENTAIS ---
if pagina == "📚 Temas & Mapas":
    st.title("📚 Temas & Mapas Mentais")
    st.caption("O EVANGELHO DO REINO")

    dados.setdefault("mapas", {})

    for mod in MODULOS_MESES:
        chave_mes = mod["chave"]
        dados["mapas"].setdefault(chave_mes, [])

        with st.expander(f"📌 {mod['tag']} - {mod['titulo']}"):
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
                    st.image(img_url, use_container_width=True)
                    if es_admin:
                        if st.button(
                            "🗑️ Excluir esta imagem",
                            key=f"del_img_{chave_mes}_{idx_img}",
                        ):
                            dados["mapas"][chave_mes].pop(idx_img)
                            salvar_dados(dados)
                            st.rerun()
            else:
                st.info("Nenhum mapa mental cadastrado para este mês.")

# --- TELA 2: PLANO DE LEITURA BÍBLICA ---
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
            dados["leitura"][mes_sel].append(
                {"texto": nova_leitura, "concluido": False}
            )
            salvar_dados(dados)
            st.rerun()

    st.divider()

    for i, item in enumerate(dados["leitura"][mes_sel]):
        col_chk, col_del = st.columns([4, 1])
        status = col_chk.checkbox(
            item["texto"],
            value=item.get("concluido", False),
            key=f"chk_{mes_sel}_{i}",
        )
        if status != item.get("concluido", False):
            dados["leitura"][mes_sel][i]["concluido"] = status
            salvar_dados(dados)

        if es_admin:
            if col_del.button("❌", key=f"del_leit_{mes_sel}_{i}"):
                dados["leitura"][mes_sel].pop(i)
                salvar_dados(dados)
                st.rerun()

# --- TELA 3: RELÓGIO DE ORAÇÃO ---
elif pagina == "⏰ Relógio de Oração":
    st.title("⏰ Relógio de Oração (Escala 30m)")

    horas = [
        f"{h:02d}:{m:02d} - {(h if m==0 else h+1)%24:02d}:{(m+30)%60:02d}"
        for h in range(24)
        for m in (0, 30)
    ]
    turno_sel = st.selectbox("Selecione o Turno", horas)

    if turno_sel not in dados["oracao"]:
        dados["oracao"][turno_sel] = []

    if es_admin:
        with st.form(f"form_oracao_{turno_sel}"):
            c1, c2 = st.columns(2)
            cargo = c1.selectbox("Cargo", CARGOS_DISPONIVEIS)
            nome = c2.text_input("Nome do Intercessor")
            if st.form_submit_button("➕ Adicionar Intercessor") and nome:
                dados["oracao"][turno_sel].append(
                    {"cargo": cargo, "nome": nome}
                )
                salvar_dados(dados)
                st.rerun()

    st.subheader(f"Intercessores do turno {turno_sel}:")
    for i, item in enumerate(dados["oracao"][turno_sel]):
        c_txt, c_del = st.columns([4, 1])
        c_txt.write(f"🙏 **[{item['cargo']}]** {item['nome']}")
        if es_admin and c_del.button("❌", key=f"del_or_{turno_sel}_{i}"):
            dados["oracao"][turno_sel].pop(i)
            salvar_dados(dados)
            st.rerun()

# --- TELA 4: CALENDÁRIO DE JEJUM ---
elif pagina == "🗓️ Calendário de Jejum":
    st.title("🗓️ Calendário Semanal de Jejum")

    dias = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]
    dia_sel = st.selectbox("Selecione o Dia da Semana", dias)

    if dia_sel not in dados["jejum"]:
        dados["jejum"][dia_sel] = []

    if es_admin:
        with st.form(f"form_jejum_{dia_sel}"):
            c1, c2 = st.columns(2)
            cargo = c1.selectbox("Cargo", CARGOS_DISPONIVEIS)
            nome = c2.text_input("Nome da Pessoa")
            if st.form_submit_button("➕ Adicionar ao Jejum") and nome:
                dados["jejum"][dia_sel].append({"cargo": cargo, "nome": nome})
                salvar_dados(dados)
                st.rerun()

    st.subheader(f"Escala de Jejum - {dia_sel}:")
    for i, item in enumerate(dados["jejum"][dia_sel]):
        c_txt, c_del = st.columns([4, 1])
        cargo_txt = f"[{item['cargo']}] " if item.get("cargo") else ""
        c_txt.write(f"🍞 **{cargo_txt}**{item['nome']}")
        if es_admin and c_del.button("❌", key=f"del_j_{dia_sel}_{i}"):
            dados["jejum"][dia_sel].pop(i)
            salvar_dados(dados)
            st.rerun()

# --- TELA 5: DISCIPULADORES ---
elif pagina == "👥 Discipuladores":
    st.title("👥 Encontro dos Discipuladores")

    if es_admin:
        with st.expander("➕ Cadastrar Novo Discipulador"):
            with st.form("form_discipulador"):
                c1, c2 = st.columns(2)
                cargo = c1.selectbox("Cargo", CARGOS_DISPONIVEIS)
                nome = c2.text_input("Nome do Discipulador(a)")
                dia = c1.text_input("Dia do Encontro (ex: Terça-feira)")
                horario = c2.text_input("Horário (ex: 19:30)")
                foto_file = st.file_uploader(
                    "Foto do Discipulador", type=["png", "jpg", "jpeg"]
                )

                if st.form_submit_button("Salvar Discipulador") and nome:
                    url_foto = ""
                    if foto_file:
                        caminho_foto = f"discipuladores/{nome}_{foto_file.name}"
                        url_foto = upload_imagem(foto_file, caminho_foto)

                    dados["discipuladores"].append(
                        {
                            "cargo": cargo,
                            "nome": nome,
                            "dia": dia,
                            "horario": horario,
                            "foto": url_foto,
                            "participantes": [],
                        }
                    )
                    salvar_dados(dados)
                    st.success("Discipulador cadastrado com sucesso!")
                    st.rerun()

    st.divider()

    for idx, disc in enumerate(dados["discipuladores"]):
        disc.setdefault("participantes", [])

        with st.container():
            col_img, col_info, col_p = st.columns([1, 2, 2])

            # Foto
            if disc.get("foto"):
                col_img.image(disc["foto"], width=120)
            else:
                col_img.write("👤 *Sem Foto*")

            # Informações do Discipulador
            col_info.subheader(f"{disc.get('cargo', '')} {disc['nome']}")
            col_info.write(
                f"📅 **Dia:** {disc.get('dia', '')} às {disc.get('horario', '')}"
            )
            col_info.write(f"👥 **Participantes:** {len(disc['participantes'])}")

            if es_admin:
                if col_info.button(
                    "🗑️ Remover Discipulador", key=f"del_disc_{idx}"
                ):
                    dados["discipuladores"].pop(idx)
                    salvar_dados(dados)
                    st.rerun()

            # Visualizar e Adicionar Participantes
            with col_p.expander(
                f"👥 Ver Participantes ({len(disc['participantes'])})"
            ):
                for p_idx, part in enumerate(disc["participantes"]):
                    cp_txt, cp_del = st.columns([3, 1])
                    cp_txt.write(
                        f"• [{part.get('cargo', 'Membro')}] {part['nome']}"
                    )
                    if es_admin and cp_del.button(
                        "❌", key=f"del_part_{idx}_{p_idx}"
                    ):
                        disc["participantes"].pop(p_idx)
                        salvar_dados(dados)
                        st.rerun()

                if es_admin:
                    st.caption("Adicionar Participante:")
                    p_cargo = st.selectbox(
                        "Cargo", CARGOS_DISPONIVEIS, key=f"pcargo_{idx}"
                    )
                    p_nome = st.text_input("Nome", key=f"pnome_{idx}")
                    if (
                        st.button("➕ Adicionar Membro", key=f"btn_p_{idx}")
                        and p_nome
                    ):
                        disc["participantes"].append(
                            {"cargo": p_cargo, "nome": p_nome}
                        )
                        salvar_dados(dados)
                        st.rerun()
        st.divider()
