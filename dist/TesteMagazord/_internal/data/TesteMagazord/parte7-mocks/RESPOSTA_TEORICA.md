## Questão 7.1 - Mocks de APIs Externas

📖 Contexto  
Seu sistema integra com marketplaces (Mercado Livre, Amazon) via API para:

- Publicar produtos
- Atualizar preços
- Processar pedidos
- Atualizar estoque

💭 Perguntas Teóricas  

### 7.1.a) Como você testaria essas integrações sem afetar os ambientes reais?
Eu evitaria testar diretamente nos ambientes reais do Mercado Livre e da Amazon, porque isso pode gerar impactos no negócio, como publicação de produtos indevidos, alteração de preços ou geração de pedidos falsos. Além disso, depender de serviços externos deixa os testes instáveis e difíceis de reproduzir. Por isso, eu trabalharia em camadas. No dia a dia, a maior parte dos testes rodaria com mocks ou stubs das APIs, simulando as respostas. Assim os testes ficam rápidos, previsíveis e independentes de terceiros, ideais para CI.

### 7.1.b) Como implementaria uma estratégia de mock para simular respostas?
Eu não trataria mock só como “simular retorno”, mas como parte da arquitetura de testes. Primeiro, basearia os mocks no contrato real da API, para garantir que request e response sigam o mesmo padrão do serviço oficial. Isso evita criar um mock que funciona no teste, mas quebra em produção. Depois, criaria cenários que representem situações reais do dia a dia, como sucesso, erro de validação, token expirado, indisponibilidade, timeout e rate limit. Assim conseguimos testar não só o caminho feliz, mas também como o sistema se comporta em falhas ou situações inesperadas.