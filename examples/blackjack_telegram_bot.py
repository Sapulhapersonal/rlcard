# Bot de Blackjack para Telegram (exemplo básico)
# Instale a dependência: pip install python-telegram-bot

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import rlcard
import random
import rlcard

TOKEN = "8250766591:AAGPj2AI1csUSd5w4l_9Xe1adY-DpfZbJ00"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Inicializa placar do usuário
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    for k in ['vitorias', 'derrotas', 'empates']:
        if context.user_data.get(k) is None:
            context.user_data[k] = 0
    if update.message:
        await update.message.reply_text("Bem-vindo ao Blackjack! Digite /jogar para começar.")

async def jogar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mantém placar entre rodadas
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    for k in ['vitorias', 'derrotas', 'empates']:
        if context.user_data.get(k) is None:
            context.user_data[k] = 0
    env = rlcard.make('blackjack')
    state = env.reset()
    if isinstance(state, tuple):
        state = state[0]
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data.clear()
    context.user_data['env'] = env
    context.user_data['state'] = state
    context.user_data['ativo'] = True
    obs = state['raw_obs']
    cartas_jogador = obs.get('player0 hand', [])
    cartas_dealer = obs.get('dealer hand', [])
    if update.message:
        if cartas_jogador:
            await update.message.reply_text(
                f"Suas cartas: {', '.join(cartas_jogador)}\n"
                f"Cartas do dealer: {', '.join(cartas_dealer)}\n"
                "Ações: 0 - hit, 1 - stand\nDigite o número da ação."
            )
        else:
            await update.message.reply_text(f"Estado inesperado: {obs}")

async def acao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data is None:
        context.user_data = {}
    user_data = context.user_data
    # Inicializa placar se necessário
    for k in ['vitorias', 'derrotas', 'empates']:
        if k not in user_data or user_data[k] is None:
            user_data[k] = 0
    user_data = context.user_data
    # Inicializa placar se necessário
    for k in ['vitorias', 'derrotas', 'empates']:
        if user_data.get(k) is None:
            user_data[k] = 0
    # Inicializa placar se necessário
    for k in ['vitorias', 'derrotas', 'empates']:
        if user_data.get(k) is None:
            user_data[k] = 0
    # Função para atualizar placar
    def atualizar_placar(explicacao):
        if 'venceu' in explicacao:
            user_data['vitorias'] += 1
        elif 'derrota' in explicacao or 'Dealer venceu' in explicacao:
            user_data['derrotas'] += 1
        elif 'Empate' in explicacao:
            user_data['empates'] += 1
    if not update.message:
        return
    texto = update.message.text
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    user_data = context.user_data
    if not user_data.get('ativo'):
        await update.message.reply_text("Use /jogar para iniciar uma nova partida.")
        return
    env = user_data.get('env')
    state = user_data.get('state')
    if env is None or state is None:
        await update.message.reply_text("Erro interno. Use /jogar para reiniciar.")
        return
    legal_actions = list(state['legal_actions'].keys())
    if texto not in [str(i) for i in range(len(legal_actions))]:
        await update.message.reply_text("Ação inválida. Digite 0 ou 1.")
        return
    action = legal_actions[int(texto)]
    result = env.step(action)
    if len(result) == 4:
        next_state, reward, done, _ = result
    else:
        next_state, reward = result
        done = False
    user_data['state'] = next_state
    obs = next_state['raw_obs']
    def format_carta(carta):
        # Exemplo: 'SK' -> 'K♠', 'H5' -> '5♥'
        if len(carta) == 2:
            naipe = carta[0]
            valor = carta[1]
        elif len(carta) == 3:  # Para 10
            naipe = carta[0]
            valor = carta[1:]
        else:
            return carta
        naipes = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
        figuras = {'A': 'A', 'J': 'J', 'Q': 'Q', 'K': 'K'}
        valor_formatado = figuras.get(valor, valor)
        return f"{valor_formatado}{naipes.get(naipe, naipe)}"

    def calcular_pontuacao(cartas):
        valores = {'A': 1, 'J': 10, 'Q': 10, 'K': 10}
        total = 0
        ases = 0
        for c in cartas:
            v = c[1:] if len(c) > 2 else c[1]
            v = v.strip()
            if v == 'A':
                total += 1
                ases += 1
            elif v in valores:
                total += valores[v]
            elif v.isdigit():
                total += int(v)
            else:
                continue  # ignora valores inesperados
        # Ajusta Ás para 11 se não estourar
        for _ in range(ases):
            if total + 10 <= 21:
                total += 10
        return total

    cartas_jogador_raw = obs.get('player0 hand', [])
    cartas_dealer_raw = obs.get('dealer hand', [])
    cartas_jogador = [format_carta(c) for c in cartas_jogador_raw]
    cartas_dealer = [format_carta(c) for c in cartas_dealer_raw]
    pont_jogador = calcular_pontuacao(cartas_jogador_raw)
    pont_dealer = calcular_pontuacao(cartas_dealer_raw)

    def resultado_blackjack(pont_jogador, pont_dealer, reward):
        if pont_jogador > 21:
            return "Você estourou! Derrota."
        elif pont_dealer > 21:
            return "Dealer estourou! Você venceu."
        elif pont_jogador == pont_dealer:
            return "Empate."
        elif pont_jogador > pont_dealer:
            return "Você venceu!"
        else:
            return "Dealer venceu."

    # Se o jogador estourou, finaliza imediatamente
    if pont_jogador >= 21:
        user_data['ativo'] = False
        explicacao = resultado_blackjack(pont_jogador, pont_dealer, reward)
        atualizar_placar(explicacao)
        motivo = "Você atingiu 21!" if pont_jogador == 21 else "Você estourou!"
        await update.message.reply_text(
            f"{motivo}\nFim do jogo!\nSuas cartas finais: {', '.join(cartas_jogador)} (pontuação: {pont_jogador})\n"
            f"Cartas do dealer: {', '.join(cartas_dealer)} (pontuação: {pont_dealer})\n"
            f"{explicacao}\nResultado numérico: {reward}\n"
            f"Placar: {user_data['vitorias']} vitória(s), {user_data['derrotas']} derrota(s), {user_data['empates']} empate(s).\n"
            "Deseja jogar outra rodada? Envie /jogar para continuar ou /sair para encerrar."
        )
        return
    if done:
        user_data['ativo'] = False
        if cartas_jogador:
            explicacao = resultado_blackjack(pont_jogador, pont_dealer, reward)
            atualizar_placar(explicacao)
            await update.message.reply_text(
                f"Fim do jogo!\nSuas cartas finais: {', '.join(cartas_jogador)} (pontuação: {pont_jogador})\n"
                f"Cartas do dealer: {', '.join(cartas_dealer)} (pontuação: {pont_dealer})\n"
                f"{explicacao}\nResultado numérico: {reward}\n"
                f"Placar: {user_data['vitorias']} vitória(s), {user_data['derrotas']} derrota(s), {user_data['empates']} empate(s).\n"
                "Deseja jogar outra rodada? Envie /jogar para continuar ou /sair para encerrar."
            )
        else:
            await update.message.reply_text(f"Fim do jogo! Estado inesperado: {obs}\nResultado: {reward}\nUse /jogar para começar novamente.")
    else:
        if cartas_jogador:
            opcoes = []
            if pont_jogador < 21:
                opcoes.append("0 - hit")
                opcoes.append("1 - stand")
            await update.message.reply_text(
                f"Você escolheu {'hit' if texto == '0' else 'stand'}.\n"
                f"Suas cartas: {', '.join(cartas_jogador)} (pontuação: {pont_jogador})\n"
                f"Cartas do dealer: {', '.join(cartas_dealer)} (pontuação: {pont_dealer})\n"
                f"Ações disponíveis: {', '.join(opcoes)}\nDigite o número da ação."
            )
        else:
            await update.message.reply_text(f"Você escolheu {'hit' if texto == '0' else 'stand'}. Estado inesperado: {obs}\nAções: 0 - hit, 1 - stand\nDigite o número da ação.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jogar", jogar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, acao))
    print("Bot pronto! Execute este script e converse com seu bot no Telegram.")
    app.run_polling()
