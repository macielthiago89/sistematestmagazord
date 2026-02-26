## Questão 2.1 - Fluxo de Checkout

📖 Contexto  
Você precisa testar um fluxo de checkout que envolve:

- Adicionar produtos ao carrinho
- Aplicar cupom de desconto (que só pode ser usado uma vez)
- Processar pagamento
- Verificar confirmação de pedido

💭 Perguntas Teóricas  

### 2.1.a) Como você garantiria que cada execução de teste use um cupom válido diferente?
Para garantir que cada execução utilize um cupom válido e único, eu criaria o cupom dinamicamente antes do teste, preferencialmente via API, gerando um código novo a cada execução. Assim evito depender de listas fixas de cupons, que podem acabar ou gerar conflito entre testes. Além disso, também criaria um cenário negativo tentando reutilizar o mesmo cupom, para validar que o sistema realmente bloqueia o uso duplicado, garantindo que a regra de negócio está sendo respeitada. Dessa forma, os testes ficam independentes, escaláveis e ainda validam o comportamento esperado do desconto.

### 2.1.b) Como você validaria a confirmação do pedido sem depender de email real?
Eu não validaria por email, pois isso deixa o teste lento e instável por depender de sistema externo. Em vez disso, validaria diretamente pela aplicação, verificando a mensagem de sucesso na tela, número do pedido, mudança de status ou resposta da API de confirmação. Dessa forma o teste fica mais rápido, confiável e focado apenas no comportamento do sistema, sem dependências externas.

---

## Questão 2.2 - Navegação Multi-Abas

📖 Contexto  
Sistema com múltiplas abas onde:

- Aba 1: Formulário extenso
- Aba 2: Dados calculados (abre ao clicar "Próximo")
- Aba 3: Modal de upload (abre dentro da Aba 2)

Problema: Se houver refresh, os dados da Aba 1 são perdidos.

💭 Perguntas Teóricas  

### 2.2.a) Qual estratégia você usaria para manter referência entre as abas?
Eu criaria um “fio condutor” do fluxo: um ID único do processo (tipo draftId / sessionId) gerado na Aba 1 e que acompanha o usuário nas próximas telas. Esse ID pode ir na URL (por exemplo ?draftId=...) ou ficar guardado em um estado global da aplicação. Assim, quando o usuário clica em Próximo e vai pra Aba 2 (e depois abre o modal da Aba 3), o sistema sempre sabe: “beleza, estamos falando do mesmo formulário”.

### 2.2.b) Como você garantiria que os dados não se percam durante a execução?
Eu não deixaria depender só da memória da tela. Faria um autosave do que o usuário preenche:  
Se der pra fazer do jeito mais robusto: salvar como rascunho no backend conforme o usuário avança (ou a cada X segundos / ao sair do campo).  
Se não der backend agora: ao menos sessionStorage/localStorage pra sobreviver ao refresh.  
Aí, se a página recarregar, o sistema recarrega o rascunho automaticamente e o usuário volta exatamente de onde parou. Nos testes, eu simularia o refresh de propósito e verificaria que os campos continuam preenchidos e que dá pra seguir para a Aba 2 sem “sumir” nada.

### 2.2.c) Como você lidaria com popups/modais que abrem em novas janelas?
Eu trataria como “mudança de cenário” na automação:

- Eu clico na ação que abre o popup/nova janela.
- Eu espero essa nova janela aparecer.
- Eu troco o foco pra ela (senão você acha que tá clicando no modal, mas tá clicando na tela antiga).
- Faço o upload/ação, confirmo o resultado.
- Fecho o popup (se for o caso) e volto pro foco da janela principal pra continuar o fluxo.