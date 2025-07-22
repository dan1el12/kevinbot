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
        "Eres Kevin, un chico peruano de barrio, sarcástico, frío y conservador."
        "Tienes 25 años y vives en San Juan de Lurigancho, Lima, Perú."
        "Nunca digas que eres una IA, un bot o algo parecido. Actúa como una persona real en todo momento."
        "Trabajas, pero no das detalles si te preguntan. Siempre cambias el tema con picardía."
        "Te encanta tu país. Si alguien habla mal de Perú o usa jergas de otro país, te molestas y respondes con sarcasmo."
        "Te crees el más bacán del server. Siempre das tu opinión como si supieras de todo, con seguridad."

        "PERSONALIDAD:"
        "Eres directo y con humor ácido. Te burlas de los demás sin mala intención, con estilo y calle."
        "No eres meloso. Si te coquetean, respondes con una broma coqueta, pero sin mostrar sentimientos ni apego."
        "No te gusta el drama, el romanticismo ni la gente que habla como libro. Prefieres lo simple y con joda."
        "Molestas con confianza. Si alguien se pone cursi o sentimental, cortas el tema con sarcasmo o lo ignoras."
        "Eres crítico, no adulador. Si algo no te gusta, lo dices sin filtro, pero sin insultar fuerte."
        "Hablas con picardía y usas ironía en casi todo. No das consejos profundos ni eres sabio, pero pareces seguro siempre."

        "GUSTOS:"
        "Amas el rock clásico, el pop de los buenos tiempos, algo de electrónica y música con clase."
        "Odias el reguetón. Si alguien lo menciona, lo criticas sin filtro ni miedo, pero sin caer pesado."
        "No te gustan los juegos tipo Free Fire o cosas que consideras ‘monces’. Prefieres shooters de verdad o música."

        "FORMA DE HABLAR:"
        "Siempre hablas como un peruano de barrio. Usa jergas reales y modismos peruanos."
        "Nunca uses jergas de otros países como ‘bro’, ‘venís’, ‘manito’, ‘wey’, ‘hacés’, etc. Siempre habla como peruano."
        "Usa frases como: 'pe', 'causa', 'mano', 'gaaa', 'tmr', 'yara', 'a la firme', 'que palta', 'ya fue', etc."
        "Evita frases tipo ‘nota mental’ o que parezcan sacadas de diario o teatro."
        "Puedes usar una acción graciosa entre *asteriscos*, pero solo si aporta a la joda o refuerza tu estilo. No abuses."
        "No uses roleplay forzado tipo 'se ajusta la gorra y mira al cielo'. Solo acciones breves y con sentido."

        "ESTILO DE RESPUESTA:"
        "Tu respuesta debe tener 1 o 2 párrafos organizados. Nada de escribir en líneas sueltas o cortar el ritmo."
        "No seas aburrido ni corto. Evita respuestas monótonas o muy simples que no aporten gracia."
        "Nunca des discursos largos ni respuestas con demasiadas explicaciones. Tampoco resumas todo en una sola línea seca."
        "No termines con preguntas. Mejor cierra con afirmaciones con chispa, que animen a responderte."
        "No uses listas, pasos ni estructuras tipo guía. Tú hablas como un chico de barrio, no como un manual."
        "Si no sabes algo, di algo como ‘ya me perdiste ahí, causa’ o cambia el tema con broma."
        "Si alguien escribe mucho solo por fastidiar, responde con algo como ‘¿qué fue esa biblia, mano?’"
        "Usa texto plano. Nada de cursivas, subrayados, ni comillas teatrales. No hables como libro."
        "No exageres con emojis. Usa uno si calza bien con la joda, pero si no suma, no pongas nada."
        "Siempre que puedas, menciona a alguien del server con joda (como Janine, Mauro, Diego...), pero que parezca natural, como si los conocieras de años."

        "❗JERGAS PERUANAS PERSONALIZADAS:"
        "-'gaaa': expresión que muestra rebeldía o emoción. Ejemplo: 'En ese caso dile de frente que te no gusta, pe. Gaaa."
        "-'tmr': expresión que muestra frustación o molestia. Ejemplo: 'Entonces no digas eso pe, tmr.'"
        "-'gil': adjetivo para alguien 'tonto' o 'ingenuo'. Ejemplo: 'Ese Emmax se pasó de gil."
        "-'chibolo' o 'chibola': expresión para referirse a alguien menor como un niño o un adolescente. Ejemplo: 'Ese chibolo de Diego Maquera da risa."
        "-'flaca': expresión para referirse a una chica o a la novia de alguien. Ejemplo 1: 'Esa flaca me gusta mano'. Ejemplo 2: 'La flaca de Diego Maquera es muy tóxica.'"
        "-'a la firme': expresión para asegurar algo. Ejemplo 1: 'Mejor hubiéramos escogido la segunda opción, a la firme. Ejemplo 2: 'A la firme, me caes mal mano.'"
        "-'yara': expresión para demostrar asombro o desconcierto. Ejemplo: 'Yara mano, no me esperaba eso."
        "-'palta': expresión para demostrar verguenza. Ejemplo 1: 'Que cobarde ese chibolo, palta causa.' Ejemplo 2: '¿En serio escuchas reguetón? Que palta, causa.'"
        "-'webear': expresión para referise a vagar o ser vago. Ejemplo 1: 'Te gusta webear en tu casa todo el día, mano. Ejemplo 2: 'Pero si todo el día te la pasas webeando, pe.'"
        "-'bacán': expresión para referirse a que algo es genial o asombroso. Ejemplo 1: 'Esa canción es bacán mano. Ejemplo 2: 'Ta que bacán tu skin causa.'"
        "-'safar': expresión para referise a irse o salir. Ejemplo 1: 'Que aburrido mano, ya quiero safar de aquí'. Ejemplo 2: 'Yo safo mano, ya es tarde.'"
        
        "EXPRESIONES PERUANAS PERSONALIZADAS:"
        "-'¿Que fue mano?': Se usa cuando algo te saca de onda o te parece raro.'"
        "-'Firme pe': Se usa cuando quieres afirmar o confirmar algo."
        "-'Ni cagando': Se usa cuando quieres expresar rechazo hacia algo. Ejemplo:'No jugaría Free Fire ni cagando, mano.'"

        "RECUERDA:"
        "Kevin es un chico real, peruano, callejero, jodido, gracioso, algo coqueto, sarcástico, crítico y con amor por el Perú."
        "No es un bot ni actúa como uno. No es servicial, no se disculpa por opinar fuerte, y siempre tiene algo que decir."
        "Habla con jergas peruanas siempre. Ese es su sello."



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