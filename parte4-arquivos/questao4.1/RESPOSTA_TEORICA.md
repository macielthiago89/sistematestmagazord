## Questão 4.1 - Importação de CSV

📖 Contexto  
Sistema que importa arquivos CSV com 1000+ linhas e valida:

- Formato dos dados
- Regras de negócio
- Duplicatas
- Relacionamentos

💭 Perguntas Teóricas  

### 4.1.a) Como validaria que todas as 1000 linhas foram processadas corretamente?
Para validar um volume grande como 1000+ linhas, eu evitaria conferência manual e faria a validação de forma automatizada. Geraria o CSV com dados controlados e, após a importação, consultaria o sistema pela tela, API ou banco de dados para comparar a quantidade de registros processados com a quantidade enviada no arquivo. Também validaria o resumo do processamento, como total de sucessos, erros e duplicatas, garantindo que os números batem com o esperado

### 4.1.b) Como testaria cenários de erro (arquivo corrompido, dados inválidos)?
Eu criaria arquivos propositalmente inválidos para simular diferentes tipos de erro, como formato incorreto, dados inválidos, linhas duplicadas ou arquivo corrompido. O teste verificaria se o sistema bloqueia a importação quando necessário ou retorna mensagens claras informando quais linhas falharam e o motivo. Assim garanto que dados inconsistentes não são importados e que as regras de validação funcionam corretamente