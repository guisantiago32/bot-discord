import discord
from discord.ext import commands
import json
import os

from tickets import (
    TicketView,
    TicketCloseView,
    registrar_ticket_comando
)

TOKEN = "MTU1MjgwNDE1NjU3MjU2OTYyMQ.GFdwO9.cDpl_8THLGwJbB5DIYjOGisLZ1LrYvB7Hsui2E"
CANAL_LOGS = 1538271493581054033
ARQUIVO = "metas.json"

intents = discord.Intents.default()
intents.message_content = True  

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

metas_pendentes = {}


def carregar_metas():
    if not os.path.exists(ARQUIVO):
        return []

    with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_metas(metas):
    with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(
            metas,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


class MetaModal(discord.ui.Modal, title="Registrar Meta Paga"):

    id_membro = discord.ui.TextInput(
        label="ID",
        placeholder="Digite o ID",
        max_length=20
    )

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Digite o nome",
        max_length=50
    )

    meta = discord.ui.TextInput(
        label="Meta que entregou",
        placeholder="Ex: 100 unidades",
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):

        metas_pendentes[interaction.user.id] = {
            "id": str(self.id_membro.value),
            "nome": str(self.nome.value),
            "meta": str(self.meta.value),
            "canal": interaction.channel.id
        }

        await interaction.response.send_message(
            "📸 **Envie o print agora neste canal.**\n\n"
            "Assim que você enviar a imagem, "
            "ela será registrada automaticamente.",
            ephemeral=True
        )


class MetaView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Registrar Meta",
        style=discord.ButtonStyle.success,
        emoji="🎯",
        custom_id="registrar_meta"
    )
    async def registrar_meta(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            MetaModal()
        )

    @discord.ui.button(
        label="Ver Metas Pagas",
        style=discord.ButtonStyle.primary,
        emoji="📋",
        custom_id="ver_metas"
    )
    async def ver_metas(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        metas = carregar_metas()

        if not metas:
            await interaction.response.send_message(
                "📋 **METAS PAGAS**\n\n"
                "Nenhuma meta foi registrada ainda.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📋 METAS PAGAS",
            description="Lista das metas já registradas.",
            color=discord.Color.blue()
        )

        for item in metas[-20:]:
            embed.add_field(
                name=f"👤 {item['nome']}",
                value=(
                    f"🆔 ID: `{item['id']}`\n"
                    f"🎯 Meta: **{item['meta']}**"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    

        metas = carregar_metas()

        if not metas:
            await interaction.response.send_message(
                "📋 **METAS PAGAS**\n\n"
                "Nenhuma meta foi registrada.",
                ephemeral=True
            )
            return

        texto = "📋 **METAS PAGAS**\n\n"

        for item in metas:
            texto += (
                f"✅ **{item['nome']}**\n"
                f"🆔 ID: `{item['id']}`\n"
                f"🎯 Meta: **{item['meta']}**\n\n"
            )

        await interaction.response.send_message(
            texto,
            ephemeral=True
        )


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    usuario_id = message.author.id

    if usuario_id not in metas_pendentes:
        await bot.process_commands(message)
        return

    dados = metas_pendentes[usuario_id]

    if message.channel.id != dados["canal"]:
        await bot.process_commands(message)
        return

    imagem = None

    for anexo in message.attachments:

        nome = anexo.filename.lower()

        if nome.endswith(
            (".png", ".jpg", ".jpeg", ".webp")
        ):
            imagem = anexo
            break

    if imagem is None:
        await bot.process_commands(message)
        return

    metas = carregar_metas()

    nova_meta = {
        "id": dados["id"],
        "nome": dados["nome"],
        "meta": dados["meta"],
        "print": imagem.url
    }

    metas.append(nova_meta)

    salvar_metas(metas)

    del metas_pendentes[usuario_id]

    canal_logs = bot.get_channel(CANAL_LOGS)

    if canal_logs is None:
        canal_logs = await bot.fetch_channel(
            CANAL_LOGS
        )

    embed = discord.Embed(
        title="🎯 META ENTREGUE",
        description="Uma nova meta foi registrada.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Nome",
        value=dados["nome"],
        inline=True
    )

    embed.add_field(
        name="🆔 ID",
        value=dados["id"],
        inline=True
    )

    embed.add_field(
        name="🎯 Meta",
        value=dados["meta"],
        inline=False
    )

    embed.add_field(
        name="👮 Registrado por",
        value=message.author.mention,
        inline=False
    )

    embed.set_image(
        url=imagem.url
    )

    await canal_logs.send(
        embed=embed
    )

    await message.reply(
        "✅ **Meta registrada!**\n"
        "📸 Print enviado para os logs.",
        mention_author=False
    )

    await bot.process_commands(message)


@bot.event
async def on_ready():
    print("TESTE: o bot iniciou o on_ready")

    bot.add_view(TicketView())
    bot.add_view(TicketCloseView())
    bot.add_view(MetaView())

    await bot.tree.sync()

    print(
        f"Bot conectado como {bot.user}"
    )


@bot.tree.command(
    name="painel",
    description="Envia o painel de metas"
)
async def painel(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="🎯 METAS PAGAS",
        description=(
            "Clique em **Registrar Meta** para "
            "registrar uma nova entrega.\n\n"
            "🎯 **Registrar Meta**\n"
            "Informe ID, nome e meta.\n\n"
            "📸 Depois envie o print.\n"
            "O sistema registrará automaticamente.\n\n"
            "📋 **Ver Metas Pagas**\n"
            "Veja as metas já registradas."
        ),
        color=discord.Color.green()
    )

    await interaction.channel.send(
        embed=embed,
        view=MetaView()
    )

    await interaction.response.send_message(
        "✅ Painel criado!",
        ephemeral=True
    )

registrar_ticket_comando(bot)
