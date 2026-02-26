## Questão 5.1 - Automação Mobile

📖 Contexto  
Aplicativo mobile (iOS e Android) que usa:

- Geolocalização
- Câmera
- Notificações push
- Storage offline
- Sincronização

💭 Perguntas Teóricas  

### 5.1.a) Qual ferramenta você escolheria e por quê? (Appium, Detox, Maestro, etc.)
Para esse cenário, eu avaliaria uma ferramenta multiplataforma que permitisse reaproveitar testes entre iOS e Android e tivesse boa maturidade de mercado. Provavelmente optaria pelo Appium, por ser open source, amplamente adotado e permitir uma única base de automação para as duas plataformas, o que reduz custo de manutenção e curva de aprendizado do time. Mesmo não tendo atuado diretamente com automação mobile, priorizaria uma ferramenta já consolidada no mercado e com boa documentação, facilitando a adoção e evolução da equipe

### 5.1.b) Como você mockaria geolocalização em testes automatizados?
Eu evitaria depender do GPS real do dispositivo e definiria localizações simuladas nos emuladores ou simuladores. A ideia é controlar as coordenadas durante o teste para tornar os cenários previsíveis e repetíveis, permitindo validar diferentes comportamentos de forma estável, sem depender de fatores externos.

### 5.1.c) Estratégia para executar mesmos testes em iOS e Android?
Eu estruturaria o projeto separando a lógica dos testes dos detalhes específicos da plataforma. Manteria os fluxos reutilizáveis e criaria uma camada de abstração para os elementos de cada sistema, alterando apenas os seletores quando necessário. Assim o time consegue manter uma única suíte de testes, executando em ambos os ambientes apenas mudando a configuração do dispositivo, reduzindo retrabalho e esforço de manutenção.