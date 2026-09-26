import discord

# =========================================================
# CARGOS DE ADV
# =========================================================

ADV_1 = 1523485192646561806
ADV_2 = 1523485192646561805
ADV_3 = 1523485192646561804

# =========================================================
# ARQUIVO DE DADOS
# =========================================================

import json
import os

ARQUIVO_ADVS = "advs.json"


def carregar_advs():
    if not os.path.exists(ARQUIVO_ADVS):
        return []

    with open(ARQUIVO_ADVS, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_advs(advs):
    with open(ARQUIVO_ADVS, "w", encoding="utf-8") as arquivo:
        json.dump(
            advs,
            arquivo,
            indent=4,
            ensure_ascii=False
        )
        # =========================================================
# CALCULAR NÍVEL DA ADV
# =========================================================

def calcular_adv(advs, membro_id):

    quantidade = 0

    for adv in advs:
        if adv["membro_id"] == membro_id:
            quantidade += 1

    if quantidade >= 3:
        return 3

    return quantidade + 1

    # =========================================================
# APLICAR CARGO DA ADV
# =========================================================

async def aplicar_cargo_adv(membro, nivel):

    cargos_adv = {
        1: ADV_1,
        2: ADV_2,
        3: ADV_3
    }

    # Remove cargos antigos de ADV
    for cargo_id in cargos_adv.values():

        cargo = membro.guild.get_role(cargo_id)

        if cargo and cargo in membro.roles:
            await membro.remove_roles(cargo)

    # Adiciona o novo cargo
    novo_cargo = membro.guild.get_role(
        cargos_adv[nivel]
    )

    if novo_cargo:
        await membro.add_roles(novo_cargo)

    return novo_cargo

    # =========================================================
# COMANDO /ADV
# =========================================================

CANAL_APLICAR_ADV = 1541878544374964294
CANAL_HISTORICO_ADV = 1523485194521280642
CARGOS_SUPERIORES = [
    1552444670607630518,
    1552444205580681216,
    1552443933882187796,
    1523485192705277999
]

class ConfirmarAdvView(discord.ui.View):
    def __init__(self, membro, motivo, aplicado_por):
        super().__init__(timeout=60)

        self.membro = membro
        self.motivo = motivo
        self.aplicado_por = aplicado_por

    @discord.ui.button(
        label="Confirmar ADV",
        style=discord.ButtonStyle.green,
        emoji="✅"
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        advs = carregar_advs()

        nivel = calcular_adv(
            advs,
            self.membro.id
        )

        novo_cargo = await aplicar_cargo_adv(
            self.membro,
            nivel
        )

        registro = {
            "membro_id": self.membro.id,
            "membro_nome": str(self.membro),
            "nivel": nivel,
            "motivo": self.motivo,
            "aplicado_por": self.aplicado_por.id
        }

        advs.append(registro)
        salvar_advs(advs)

        await interaction.response.send_message(
            f"✅ ADV {nivel} aplicada em {self.membro.mention}.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.red,
        emoji="❌"
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "❌ ADV cancelada.",
            ephemeral=True
        )

class AdvModal(discord.ui.Modal, title="⚠️ Aplicar ADV"):

    membro_id = discord.ui.TextInput(
       label="ID do jogo",
       placeholder="Exemplo: 5781",
       required=True
)

    motivo = discord.ui.TextInput(
        label="Motivo da ADV",
        placeholder="Digite o motivo da advertência",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        id_jogo = self.membro_id.value.strip()

        membro = None

        for usuario in interaction.guild.members:
            nome = usuario.display_name

            if id_jogo in nome:
                membro = usuario
                break

        if membro is None:
            await interaction.response.send_message(
                f"❌ Não encontrei nenhum membro com o ID {id_jogo}.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚠️ CONFIRMAR ADV",
            description="Confira os dados antes de confirmar.",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="👤 Membro",
            value=membro.mention,
            inline=False
        )

        embed.add_field(
            name="🎮 ID do jogo",
            value=id_jogo,
            inline=True
        )

        embed.add_field(
            name="📝 Motivo",
            value=self.motivo.value,
            inline=False
        )

        embed.add_field(
            name="👮 Aplicada por",
            value=interaction.user.mention,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmarAdvView(
                membro,
                self.motivo.value,
                interaction.user
            ),
            ephemeral=True
        )
        

class AdvPainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Aplicar ADV",
        style=discord.ButtonStyle.red,
        emoji="⚠️",
        custom_id="aplicar_adv"
    )
    async def aplicar_adv(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
    AdvModal()

    )

def registrar_adv_comando(bot):

    @bot.tree.command(
        name="paineladv",
        description="Envia o painel de advertências",
        guild=discord.Object(id=1523485192646561802)
    )
    async def paineladv(interaction: discord.Interaction):

        embed = discord.Embed(
            title="⚠️ SISTEMA DE ADVERTÊNCIAS",
            description=(
                "Utilize o botão abaixo para aplicar uma advertência "
                "a um membro.\n\n"
                "As advertências serão registradas e o cargo "
                "correspondente será atualizado."
            ),
            color=discord.Color.orange()
        )

        await interaction.channel.send(
            embed=embed,
            view=AdvPainelView()
        )

        await interaction.response.send_message(
            "✅ Painel de ADV criado!",
            ephemeral=True
        )

    @bot.tree.command(
        name="adv",
        description="Aplica uma ADV em um membro",
        guild=discord.Object(id=1523485192646561802)
    )
    async def adv(
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str
    ):

        autorizado = any(
            cargo.id in CARGOS_SUPERIORES
            for cargo in interaction.user.roles
        )

        if not autorizado:
            await interaction.response.send_message(
                "❌ Você não tem permissão para aplicar ADV.",
                ephemeral=True
            )
            return

        # Verifica o canal
        if interaction.channel.id != CANAL_APLICAR_ADV:
            await interaction.response.send_message(
                "❌ Este comando só pode ser usado no canal de aplicar ADV.",
                ephemeral=True
            )
            return

                
        # Embed de confirmação
        embed = discord.Embed(
            title="⚠️ CONFIRMAR ADV",
            description="Confira os dados antes de aplicar a advertência.",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="👤 Membro",
            value=membro.mention,
            inline=True
        )

        embed.add_field(
            name="📝 Motivo",
            value=motivo,
            inline=False
        )

        embed.add_field(
            name="👮 Aplicada por",
            value=interaction.user.mention,
            inline=False
        )
        await interaction.response.send_message(
              embed=embed,
               view=ConfirmarAdvView(
                membro,
                motivo,
                interaction.user
            ),
            ephemeral=True
        )

        return