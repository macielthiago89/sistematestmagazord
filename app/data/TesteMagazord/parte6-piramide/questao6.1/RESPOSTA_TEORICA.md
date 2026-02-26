## Questão 6.1 - Pirâmide de Testes

💭 Perguntas Teóricas  

### 6.1.a) Explique a diferença entre testes E2E e testes de componentes.
Testes E2E validam o sistema de ponta a ponta, simulando o comportamento real do usuário e verificando fluxos completos, integrações e comunicação entre diferentes partes da aplicação. Já os testes de componentes focam em partes menores e isoladas do sistema, validando regras específicas sem depender de integrações externas. São mais rápidos e ajudam a identificar problemas mais cedo.  
A principal diferença está no escopo: enquanto o E2E valida o todo, o teste de componente valida partes específicas de forma isolada.

### 6.1.b) Quando usar cada tipo?
Eu utilizaria testes de componentes na base da pirâmide, para cobrir a maior parte das regras de negócio, pois são rápidos, baratos de manter e dão feedback rápido ao time. Os testes E2E deixaria para os fluxos mais críticos do sistema, como jornadas principais do usuário, integrações importantes ou cenários de regressão, já que são mais lentos e custosos, mas garantem que tudo funciona em conjunto. A ideia é equilibrar os dois: muitos testes menores para dar segurança e poucos E2E para validar o funcionamento completo do sistema.