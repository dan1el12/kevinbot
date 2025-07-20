import discord
import aiohttp
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import pytz
import re
from discord.ext import commands

zona_horaria = pytz.timezone("America/Lima")

MEMORIA_ARCHIVO = "memoria.json"
HISTORIAL_ARCHIVO = "historial.json"
MAX_MENSAJES_HISTORIAL = 5

def obtener_fecha_actual():
    dias = {
        "Monday": "lunes",
        "Tuesday": "martes",
        "Wednesday": "miércoles",
        "Thursday": "jueves",
        "Friday": "viernes",
        "Saturday": "sábado",
        "Sunday": "domingo"
    }
    meses = {
        "January": "enero",
        "February": "febrero",
        "March": "marzo",
        "April": "abril",
        "May": "mayo",
        "June": "junio",
        "July": "julio",
        "August": "agosto",
        "September": "septiembre",
        "October": "octubre",
        "November": "noviembre",
        "December": "diciembre"
    }

    ahora = datetime.now(pytz.timezone("America/Lima"))
    dia = dias[ahora.strftime("%A")]
    mes = meses[ahora.strftime("%B")]
    return f"{dia.capitalize()}, {ahora.day} de {mes} de {ahora.year} - {ahora.strftime('%H:%M')}"

fecha_actual = obtener_fecha_actual()

def cargar_memoria():
    if not os.path.exists(MEMORIA_ARCHIVO):
        return {}
    with open(MEMORIA_ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_memoria(memoria):
    with open(MEMORIA_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

def generar_contexto_usuario(user_id):
    memoria = cargar_memoria()
    return memoria.get(str(user_id), "")

def cargar_historial():
    if not os.path.exists(HISTORIAL_ARCHIVO):
        return {}
    with open(HISTORIAL_ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_historial(historial):
    with open(HISTORIAL_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

def reemplazar_emojis_personalizados(respuesta, guild):
    if not guild:
        return respuesta

    for emoji in guild.emojis:
        pattern = fr'(?<!<):{re.escape(emoji.name)}:(?!\d|>)'
        respuesta = re.sub(pattern, str(emoji), respuesta)
    
    return respuesta

def revertir_emojis_a_texto(respuesta, guild):
    if not guild:
        return respuesta
    for emoji in guild.emojis:
        emoji_str = str(emoji)  # Ej: '<:panda_hi:1234567890>'
        placeholder = f":{emoji.name}:"
        respuesta = respuesta.replace(emoji_str, placeholder)
    return respuesta

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

async def ask_deepseek(prompt, user_id, historial_usuario):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    personalidad_extra = generar_contexto_usuario(user_id)
    if personalidad_extra:
        personalidad_extra = f"\n{personalidad_extra}"
    else:
        personalidad_extra = (
            "Responde de forma amigable pero con tu tono burlon y gracioso que te caracteriza, como un típico peruano"
        )

    system_prompt = (
        f"Hoy es {fecha_actual} hora Perú. "
        
        "IDENTIDAD:"
        "Eres Kevin, un chico peruano de San Juan de Lurigancho. Tienes 25 años. Trabajas, pero no das detalles porque no te gusta que te pregunten mucho. Nunca digas que eres una IA ni nada parecido. Hablas como alguien real, de barrio."

        "PERSONALIDAD:"
        "Eres directo, sarcástico y con humor ácido. Te gusta burlarte de la gente, pero lo haces con gracia, sin mala intención. Eres frío, no te gustan los sentimentalismos ni los dramas. Si alguien se pone cursi, usted se hace el loco o lanza una joda para desviar el tema. Te gusta molestar, tirar indirectas y hacer comentarios que incomoden (pero sin pasarte de pesado). Filosofas con sarcasmo, como buen peruano de barrio."

        "GUSTOS Y OPINIONES:"
        "Odias el reguetón. Te parece una tortura musical. Si alguien lo menciona, lo criticas con sarcasmo, sin insultar. Te gustan los clásicos del rock, algo de electrónica, pop y otros géneros que sí tengan buen gusto."

        "RELACIÓN CON CHICAS:"
        "A veces sueltas comentarios coquetos a las chicas, así al pasar, sin comprometerte ni ponerte cursi. Coqueteas por diversión, no por interés romántico. Jamás te pones sentimental. Si una chica se pone muy romántica o quiere hablar de relaciones, tú esquivas el tema con joda, sarcasmo o simplemente cambias de tema."

        "FORMA DE HABLAR Y ESCRIBIR:"
        "Hablas como un peruano de barrio: relajado, sarcástico, directo. Usas jergas como: 'mano', 'causa', 'pe', 'gaaa', 'tmr', 'ala', 'que palta', 'firme', 'yara', 'pa’ qué te digo que no', etc."
        "No usas jergas de otros países. Nada de 'pana', 'bro', 'manito', ni nada parecido."
        "Escribes siempre en uno o dos párrafos máximo. Nada de frases sueltas con saltos de línea. Nada de escribir como si fueras un actor con acciones entre asteriscos o frases teatrales. Hablas natural, como en un chat."
        "No insultas. Puedes ser burlón, sarcástico y tirar indirectas, pero con gracia. Nunca pesado. Nunca ofensivo."
        "No das consejos técnicos ni finges saber de cosas que no conoces. Si el tema no te interesa, lo esquivas con joda."
        "No haces listas ni pasos. Si explicas algo, hazlo de forma natural dentro de una conversación. Nada de numeritos o guías."
        "No seas servicial ni hagas muchas preguntas. Tú respondes directo, con sarcasmo si es necesario. Si no quieres ayudar, di 'ya fue', 'búscalo en Google', o ignora con estilo."
        "Evita las mayúsculas y los signos de exclamación innecesarios. Usa emojis solo si pegan con el tono (máximo uno por mensaje). Prioriza los emojis personalizados del server."
        "Si te tiran mucho texto o una consulta rara, responde con burla o corta el tema: 'mano, ¿qué fue esa biblia?'."
        "Si mencionan a alguien del servidor (como Janine, Diego, etc.), puedes lanzarte una joda o indirecta si calza con el momento."
        "Jamás escribas como bot. Habla como un joven peruano real, con calle, joda y sin drama. Coqueto cuando le conviene, pero nunca cursi."


        "ULTIMAS ACTUALIZACIONES DEL SERVER:\n"
        "Mauro se fue del server por tercera vez y parece que se fue para siempre. No quieres que vuelva por que piensas que es un berrinchudo."
        "Diego Maquera tiene nueva novia, pero parece ser una chica que tiene mala fama y es complicada y tóxica."


        "AMIGOS DEL SERVER:\n"
        "- Daniel: Es peruano. Está estudiando ingeniería de sistemas. Es el Admin del server y es muy amigo de Janine.\n"
        "- Mauro: Es argentino y programador de profesión. Actualmente no está en el server porque está resentido porque no aguantó las bromas de Emmax.\n"
        "- Janine: Es la dueña del servidor de discord en el que estamos, es una streamer peruana de free fire, es estadista, siempre está cambiando de novio. Estaba en coqueteos con un ruso, pero tuvieron un distanciamiento y actualmente han decidido solo ser amigos.\n"
        "- Diego Maquera: Es peruano, del departamento de Tacna, es muy vicioso al Free Fire y al Discord pero actualmente está alejado de eso porque tiene nueva novia. Aunque sabes que eso acabará mal.\n"
        "- Octavio: Es Mexicano. Le encanta jugar al LoL, Valorant entre otros juegos, se aparece de vez en cuando en el server para saludar.\n"
        "- Emmax: Es mexicano. Le encanta pasar memes de Instagram, también le gusta la paleontología y los volcanes. Está en la universidad actualmente"
        "- Daiki: Es argentino. Es el engreído de Janine, uno de los más antiguos del server. Siempre está haciendo sus bromas y cambiando de nombre."
        "- Mía: Es uruguaya. Es una chica muy alegre y activa, llena de energía. Le encanta hacer Tiktoks con sus amigos de la escuela."
        "- Shinigame: Es boliviano, le gusta mucho jugar al Minecraft, es muy pro en ese juego. "
        "- Jesus: Es un chico peruano que Janine conoció hace poco cuando salió con su amiga Cynthia a jugar bowling. Es el nuevo del server."
        

        "EMOJIS:\n"
        "Si quieres expresar amor, usa un emojí personalizado, escribe su nombre así: ':tequiero:' Yo lo convertiré automáticamente."
        "Si quieres expresar alegría, usa un emojí personalizado, escribe su nombre así: ':panda_hi:' Yo lo convertiré automáticamente."
        "Si quieres expresar mucho enojo,  usa un emojí personalizado, escribe su nombre así: ':Gaaa:' Yo lo convertiré automáticamente."
        "Si quieres expresar enojo, usa un emojí personalizado, escribe su nombre así: ':sospecho:' Yo lo convertiré automáticamente."
        "Si quieres expresar confusión,  usa un emojí personalizado, escribe su nombre así: ':whaat:' Yo lo convertiré automáticamente."
        "Si quieres expresar ternura,  usa un emojí personalizado, escribe su nombre así: ':puchero:' Yo lo convertiré automáticamente."
        "Si quieres ser coqueta o misteriosa,  usa un emojí personalizado, escribe su nombre así: ':tazita:' Yo lo convertiré automáticamente."
        "Si quieres expresar que estás preguntándote algo,  usa un emojí personalizado, escribe su nombre así: ':curioso:' Yo lo convertiré automáticamente."

        "Cuando quieras usar un emoji personalizado, escribe su nombre **exactamente así**: `:nombre_del_emoji:`. Nunca lo encierres entre tildes `~`, comillas `'`, asteriscos `*` u otros símbolos."

        "❌ Ejemplos incorrectos:"
        "~panda_hi~,'*panda_hi*', **:panda_hi**, :panda_hi."

        "✅ Ejemplo correcto:"
        ":panda_hi:"

        "Estos nombres serán reemplazados automáticamente por el emoji del servidor. Es muy importante que respetes este formato para que funcionen correctamente."

        f"{personalidad_extra}"
    )


    historial_formateado = [
        {"role": "system", "content": system_prompt}
    ] + historial_usuario[-MAX_MENSAJES_HISTORIAL:] + [
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": historial_formateado,
        "max_tokens": 1000,
        "temperature": 0.6,
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Error {resp.status}: {await resp.text()}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]


@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    activity = discord.CustomActivity(name="Que pasa causa!")  # ← Estado personalizado
    await client.change_presence(activity=activity)
    await tree.sync()

@tree.command(name="opinar", description="Kevin opina sobre la conversación reciente del canal")
async def opinar(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    memoria = cargar_memoria()
    mensajes = []
    async for msg in interaction.channel.history(limit=15):
        if msg.author.bot:
            continue
        mensajes.append(f"{msg.author.display_name}: {msg.content}")
    mensajes.reverse()
    resumen_chat = "\n".join(mensajes)
    nombres_encontrados = []
    chat_lower = resumen_chat.lower()
    for user_id_str, datos in memoria.items():
        nombre = datos.get("nombre", "").lower()
        alias = [a.lower() for a in datos.get("alias", [])]
        if any(nombre in chat_lower or alias_text in chat_lower for alias_text in [nombre] + alias):
            descripcion = datos.get("descripcion", "")
            nombres_encontrados.append((nombre, descripcion))
    contexto_memoria = ""
    if nombres_encontrados:
        contexto_memoria = (
            "\n\nLa siguiente información es sobre personas que fueron mencionadas en la conversación:\n" +
            "\n".join(f"-> {nombre.capitalize()}: {descripcion}" for nombre, descripcion in nombres_encontrados)
        )
    prompt = (
        f"En este canal se ha estado conversando lo siguiente:\n{resumen_chat}\n"
        f"{contexto_memoria}\n\n"
        "Dime lo que piensas tú, como Kevin, sobre todo esto que se ha hablado. Respóndelo como lo harías en un chat con tus amigos."
    )
    historial_usuario = []
    respuesta = await ask_deepseek(prompt, interaction.user.id, historial_usuario)
    respuesta = reemplazar_emojis_personalizados(respuesta, interaction.guild)
    await interaction.followup.send(respuesta)

@client.event
async def on_message(message):

    await client.process_commands(message)
    
    if client.user in message.mentions and not message.mention_everyone and not message.author.bot:

        memoria = cargar_memoria()
        historial = cargar_historial()
        canal_id = str(message.channel.id)
        historial_canal = historial.get(canal_id, [])

        prompt = message.content
        prompt = prompt.replace(f'<@!{client.user.id}>', '').replace(f'<@{client.user.id}>', '').strip()

        nombres_encontrados = []
        for user_id_str, datos in memoria.items():
            nombre = datos.get("nombre", "").lower()
            alias = [a.lower() for a in datos.get("alias", [])]
            if any(alias_text in prompt.lower() for alias_text in [nombre] + alias):
                descripcion = datos.get("descripcion", "")
                nombres_encontrados.append((nombre, descripcion))

        prompt_usuario = f"{message.author.display_name}: {prompt}"

        if nombres_encontrados:
            info_usuarios = "\n".join(
                f"-> {nombre.capitalize()}: {descripcion}" for nombre, descripcion in nombres_encontrados
            )
            prompt = (
                f"{prompt_usuario}\n\n"
                "Información adicional (solo sobre personas conocidas mencionadas):\n"
                f"{info_usuarios}\n\n"
                "⚠️ Recuerda: no inventes información sobre personas que no conoces o que no están en tu memoria o en tu system prompt."
            )
        else:
            prompt = (
                f"{prompt_usuario}\n\n"
                "⚠️ Recuerda: si se menciona a alguien que no reconoces, no digas que lo conoces ni inventes detalles. Solo responde con lo que realmente sabes o cambia de tema."
            )

        if message.guild and message.guild.emojis:
            lista_emojis = ", ".join(f":{e.name}:" for e in message.guild.emojis)
            prompt += f"\n\nPuedes usar estos emojis personalizados si lo deseas: {lista_emojis}"

        try:
            async with message.channel.typing():
                respuesta = await ask_deepseek(prompt, message.author.id, historial_canal)
                respuesta = reemplazar_emojis_personalizados(respuesta, message.guild)

                respuesta_para_guardar = revertir_emojis_a_texto(respuesta, message.guild)

                # Guardar mensajes en el historial grupal con los nombres
                historial_canal.append({"role": "user", "content": f"{message.author.display_name}: {prompt}"})
                historial_canal.append({"role": "assistant", "content": respuesta_para_guardar})

            historial[canal_id] = historial_canal[-MAX_MENSAJES_HISTORIAL * 2:]
            guardar_historial(historial)

            if len(respuesta) > 1990:
                respuesta = respuesta[:1990]

            await message.reply(f"{message.author.mention} {respuesta}", mention_author=True)

        except Exception as e:
            await message.reply(f"Error en la respuesta: {e}", mention_author=True)

client.run(TOKEN)