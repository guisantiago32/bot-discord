import discord

# =========================================================
# CONFIGURAÇÕES
# =========================================================

CARGO_EQUIPE = 1552434192762015765
CARGO_RECRUTAMENTO = 1552433533858086962


# =========================================================
# BOTÃO FECHAR TICKET
# =========================================================

class TicketCloseView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_fechar"
    )
    async def fechar_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        canal = interaction.channel
        membro = interaction.user

        # Verifica se é equipe geral
        eh_equipe = any(
            role.id == CARGO_EQUIPE
            for role in membro.roles
        )

        # Verifica se é equipe de recrutamento
        eh_recrutamento = any(
            role.id == CARGO_RECRUTAMENTO
            for role in membro.roles
        )

        # Verifica se é dono do ticket
        eh_dono = False

        if canal.name.startswith("ticket-"):
            try:
                dono_id = int(
                    canal.name.replace("ticket-", "")
                )

                eh_dono = membro.id == dono_id

            except ValueError:
                pass

        if not (eh_dono or eh_equipe or eh_recrutamento):

            await interaction.response.send_message(
                "❌ Você não pode fechar este ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Fechando ticket..."
        )

        await canal.delete(
            reason=f"Ticket fechado por {membro}"
        )


# =========================================================
# MENU DE TICKETS
# =========================================================

class TicketSelect(discord.ui.Select):

    def __init__(self):

        opcoes = [

            discord.SelectOption(
                label="Compras",
                value="compras",
                emoji="🛒",
                description="Atendimento sobre compras"
            ),

            discord.SelectOption(
                label="Entregas",
                value="entregas",
                emoji="📦",
                description="Atendimento sobre entregas"
            ),

            discord.SelectOption(
                label="Dúvidas",
                value="duvidas",
                emoji="❓",
                description="Tire suas dúvidas"
            ),

            discord.SelectOption(
                label="Suporte",
                value="suporte",
                emoji="🛠️",
                description="Problemas e suporte"
            ),

            discord.SelectOption(
                label="Recrutamento",
                value="recrutamento",
                emoji="👮",
                description="Entre para a equipe"
            )
        ]

        super().__init__(
            placeholder="Selecione o motivo do ticket...",
            min_values=1,
            max_values=1,
            options=opcoes,
            custom_id="ticket_menu"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild
        membro = interaction.user

        # =================================================
        # VERIFICA SE JÁ POSSUI TICKET
        # =================================================

        nome_canal = f"ticket-{membro.id}"

        existente = discord.utils.get(
            guild.text_channels,
            name=nome_canal
        )

        if existente:

            await interaction.response.send_message(
                f"❌ Você já possui um ticket aberto: {existente.mention}",
                ephemeral=True
            )

            return

        tipo = self.values[0]

        # =================================================
        # ESCOLHE O CARGO
        # =================================================

        if tipo == "recrutamento":

            cargo = guild.get_role(
                CARGO_RECRUTAMENTO
            )

            if cargo is None:

                await interaction.response.send_message(
                    "❌ Cargo de recrutamento não encontrado.",
                    ephemeral=True
                )

                return

        else:

            cargo = guild.get_role(
                CARGO_EQUIPE
            )

            if cargo is None:

                await interaction.response.send_message(
                    "❌ Cargo da equipe não encontrado.",
                    ephemeral=True
                )

                return

        # =================================================
        # PERMISSÕES
        # =================================================

        permissoes = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            membro:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True
                ),

            cargo:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True
                ),

            guild.me:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True
                )
        }

        # =================================================
        # CATEGORIA
        # =================================================

        categoria = interaction.channel.category

        # =================================================
        # CRIA O TICKET
        # =================================================

        canal = await guild.create_text_channel(

            name=nome_canal,

            overwrites=permissoes,

            category=categoria,

            reason=f"Ticket de {tipo} - {membro}"
        )

        # =================================================
        # TÍTULO
        # =================================================

        titulos = {

            "compras": "🛒 TICKET DE COMPRAS",

            "entregas": "📦 TICKET DE ENTREGAS",

            "duvidas": "❓ TICKET DE DÚVIDAS",

            "suporte": "🛠️ TICKET DE SUPORTE",

            "recrutamento": "👮 TICKET DE RECRUTAMENTO"
        }

        titulo = titulos[tipo]

        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(

            title=titulo,

            description=(
                f"Olá {membro.mention}!\n\n"
                "Seu atendimento foi aberto.\n"
                "Aguarde um membro da equipe.\n\n"
                "Quando terminar o atendimento, "
                "clique em **🔒 Fechar Ticket**."
            ),

            color=discord.Color.blurple()
        )

        embed.add_field(
            name="👤 Usuário",
            value=membro.mention,
            inline=True
        )

        embed.add_field(
            name="📌 Atendimento",
            value=titulo,
            inline=True
        )

        # =================================================
        # ENVIA A MENSAGEM
        # =================================================

        await canal.send(
            content=membro.mention,
            embed=embed,
            view=TicketCloseView()
        )

        await interaction.response.send_message(
            f"✅ Ticket criado: {canal.mention}",
            ephemeral=True
        )


# =========================================================
# PAINEL
# =========================================================

class TicketView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            TicketSelect()
        )


# =========================================================
# COMANDO PARA ENVIAR O PAINEL
# =========================================================

def registrar_ticket_comando(bot):

    @bot.tree.command(
        name="ticket",
        description="Envia o painel de tickets"
    )
    async def ticket(
        interaction: discord.Interaction
    ):

        embed = discord.Embed(

            title="🎫 CENTRAL DE ATENDIMENTO",

            description=(
                "Selecione abaixo o motivo do seu atendimento.\n\n"

                "🛒 **Compras**\n"
                "Atendimento relacionado a compras.\n\n"

                "📦 **Entregas**\n"
                "Atendimento relacionado a entregas.\n\n"

                "❓ **Dúvidas**\n"
                "Tire suas dúvidas.\n\n"

                "🛠️ **Suporte**\n"
                "Problemas ou suporte.\n\n"

                "👮 **Recrutamento**\n"
                "Entre para a equipe."
            ),

            color=discord.Color.blurple()
        )

        await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "✅ Painel de tickets criado!",
            ephemeral=True
        )