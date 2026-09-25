import discord
from discord.ext import commands

from metas import (
    MetaView,
    CANAL_LOGS,
    carregar_metas,
    salvar_metas,
    metas_pendentes
)

from tickets import (
    TicketView,
    TicketCloseView,
    registrar_ticket_comando
)

# =========================================================
# CONFIGURAÇÕES
# =========================================================
import os

TOKEN = os.getenv("DISCORD_TOKEN")


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# EVENTO: BOT ONLINE
# =========================================================

@bot.event
async def on_ready():
    print("TESTE: o bot iniciou o on_ready")

    bot.add_view(MetaView())
    bot.add_view(TicketView())
    bot.add_view(TicketCloseView())

    guild = discord.Object(id=1523485192646561802)
    await bot.tree.sync(guild=guild)

    print("COMANDOS SINCRONIZADOS NO SERVIDOR")
    print(f"Bot conectado como {bot.user}")

# =========================================================
# REGISTRAR META
# =========================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    usuario_id = message.author.id

    # Verifica se o usuário está aguardando o print da meta
    if usuario_id in metas_pendentes:

        dados = metas_pendentes[usuario_id]

        # Confirma se está no mesmo canal
        if message.channel.id == dados["canal"]:

            imagem = None

            for anexo in message.attachments:

                nome = anexo.filename.lower()

                if nome.endswith(
                    (".png", ".jpg", ".jpeg", ".webp")
                ):
                    imagem = anexo
                    break

            # Se encontrou uma imagem
            if imagem:

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

                # Canal de logs
                canal_logs = bot.get_channel(CANAL_LOGS)

                if canal_logs is None:

                    try:
                        canal_logs = await bot.fetch_channel(
                            CANAL_LOGS
                        )

                    except Exception as erro:

                        print(
                            f"Erro ao encontrar canal de logs: {erro}"
                        )

                        await bot.process_commands(message)
                        return

                # Embed do log
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

                # Apaga o print do canal
                try:

                    await message.delete()

                except discord.Forbidden:

                    print(
                        "❌ O bot não tem permissão para apagar mensagens."
                    )

                await bot.process_commands(message)
                return

    await bot.process_commands(message)


# =========================================================
# COMANDO /PAINEL
# =========================================================

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
            "Clique em **🎯 Registrar Meta** "
            "para registrar uma nova entrega.\n\n"

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
        "✅ Painel de metas criado!",
        ephemeral=True
    )


# =========================================================
# COMANDO DE TICKETS
# =========================================================

registrar_ticket_comando(bot)


# =========================================================
# INICIAR BOT
# =========================================================

bot.run(TOKEN)