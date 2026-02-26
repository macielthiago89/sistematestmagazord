📖 Contexto  
Você precisa testar uma API REST que possui rate limiting de 100 requisições por minuto.

💭 Perguntas Teóricas  

### 1.1.a) Como você estruturaria seus testes automatizados para validar que o rate limiting está funcionando corretamente?
Para validar o rate limiting, eu criaria testes automatizados no Robot Framework fazendo várias requisições dentro do mesmo minuto, próximas do limite configurado (100 chamadas). Usaria loops para disparar as requisições e validaria automaticamente o status code e os headers de controle. A ideia é garantir que, enquanto estou dentro do limite, todas as chamadas funcionem normalmente, sem bloqueio, e que os headers mostrem a quantidade restante diminuindo a cada requisição. Depois da janela de tempo, a contagem deve voltar ao normal. Esses testes rodariam automaticamente no pipeline para evitar regressões.

### 1.1.b) Como você testaria o comportamento da API quando o limite é excedido?
Para testar quando o limite é ultrapassado, eu enviaria mais requisições do que o permitido, por exemplo 120 no mesmo minuto. Validaria que as primeiras são aceitas e que, após atingir o limite, a API começa a retornar erro de bloqueio (como 429). Também verificaria se ela informa quando posso tentar novamente. Em seguida, aguardaria o tempo de reset e faria novas chamadas para confirmar que o acesso volta ao normal.

---

📖 Contexto  
Uma API retorna um token JWT que expira em 15 minutos. Seus testes demoram 45 minutos para executar e fazem múltiplas chamadas autenticadas.

💭 Perguntas Teóricas  

### 1.2.a) Como você implementaria um mecanismo de refresh token automático?
Eu criaria um helper de autenticação no Robot Framework responsável por fazer login e guardar o token junto com o horário de expiração. Antes de cada requisição autenticada, o teste verifica se o token ainda é válido. Se estiver perto de expirar, faz um novo login automaticamente e atualiza o token. Assim os testes continuam rodando sem falhar por expiração e não é preciso renovar manualmente

### 1.2.b) Como você garantiria que testes executados em paralelo não conflitem no gerenciamento de tokens?
Para execuções em paralelo, eu não compartilharia o mesmo token entre testes. Cada teste teria sua própria sessão de autenticação e seu próprio token. Dessa forma um teste não interfere no outro, evitando sobrescrita de dados ou falhas aleatórias. Isso deixa a execução mais estável e previsível.