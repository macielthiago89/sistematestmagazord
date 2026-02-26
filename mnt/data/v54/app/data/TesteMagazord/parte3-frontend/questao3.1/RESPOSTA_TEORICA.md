📖 Contexto  
Sistema ExtJS onde todos os IDs são gerados dinamicamente:

- `textfield-1234-inputEl`
- `button-5678-btnEl`

Os números mudam a cada renderização

💭 Perguntas Teóricas  

### 3.1.a) Quais estratégias você utilizaria para localizar elementos de forma confiável?
Como os IDs são dinâmicos e mudam a cada renderização, eu evitaria utilizá-los nos seletores. Daria preferência para atributos mais estáveis, como name, label, placeholder, texto visível, classes fixas ou data-testid quando disponível. Também utilizaria XPath ou CSS baseados na hierarquia da tela, relacionando o campo ao seu label ou ao container pai. Se possível, ainda alinharia com o time de desenvolvimento a inclusão de identificadores estáveis voltados para automação. Assim os testes ficam menos frágeis e não quebram a cada novo render.

### 3.1.b) Como você lidaria com componentes renderizados condicionalmente?
Para elementos que aparecem apenas em determinadas ações ou condições, eu utilizaria esperas explícitas antes de interagir, validando se o elemento está presente e visível. Primeiro executaria a ação que dispara a renderização e depois aguardaria o componente carregar. Também trataria cenários onde ele pode não aparecer, para evitar falhas desnecessárias. Dessa forma o teste respeita o tempo do sistema e evita erros intermitentes.

### 3.1.c) Como identificar 1 botão específico entre 5 botões "Salvar" idênticos?
Nesse caso eu usaria o contexto da tela para diferenciar. Em vez de buscar apenas pelo texto "Salvar", eu localizaria o botão dentro de uma seção específica, formulário ou modal, usando o container pai como referência. Outra opção é usar posição relativa ou atributos adicionais. A ideia é sempre tornar o seletor mais específico ao contexto, evitando depender apenas do texto que é igual para todos.