*** Settings ***

Resource    ../main/main.robot

*** Keywords ***
#Swags labs
Adicionar o produto "Sauce Labs Backpack" ao carrinho
    Click Button    ${produtoSauceLabsBackpack}
Clique no botão "carrinho"
    Click Element    ${imagem_carrinho}
Verificar se o produto "Sauce Labs Backpack" foi adicionado ao carrinho
    Wait Until Element Is Visible    ${titulocarrinho}    timeout=10s
    Wait Until Element Is Visible   ${produtoSauceLabsBackpackcarrinho}
Clique no botão "Checkout"
    Click Button    ${btn_checkout}
Inserir o campo "First Name" com o nome do usuario
    Gerar nome aleatório
    Wait Until Element Is Visible    ${campofirstname}    timeout=10s
    Input Text    ${campofirstname}    ${nome}
Inserir o campo "Last Name" com o sobrenome do usuario
    Gerar sobrenome aleatório
    Wait Until Element Is Visible    ${campolastname}    timeout=10s
    Input Text    ${campolastname}    ${sobrenome}
Inserir o campo "Postal Code" com o cep do usuario
    Gerar CEP aleatório
    Input Text    ${campopostalcode}    ${cep}
Clique no botão "Continue"
    Click Button    ${btncontinue}
Verificar se o produto "Sauce Labs Backpack" está presente na página de checkout
    Wait Until Page Contains Element    ${titulocheckout}     timeout=5s
    Wait Until Element Is Visible    ${produtoSauceLabsBackpackcarrinho}    
Clique no botão "Finish"
    Click Button    ${btnfinish} 
Verificar se a mensagem "${mensagemsucessocheckout}" foi exibida
    ${variavelmensagemsucesso}    Replace String    ${textsucessocheckout}    $$     ${mensagemsucessocheckout}
    Wait Until Page Contains Element    ${variavelmensagemsucesso}     timeout=5s

# DEMOQA
Teste que abre nova aba via "New Tab"
    ${antes}=    Get Window Handles
    ${qtde_antes}=    Get Length    ${antes}
    Click Button    ${btnnewtab}
    ${depois}=    Get Window Handles
    ${qtde_depois}=    Get Length    ${depois}
    Should Be True    ${qtde_depois} > ${qtde_antes}
    Set Global Variable    ${depois}
    Set Global Variable    ${antes}
Navega para a nova aba
    ${novos}=    Evaluate    list(set($depois) - set($antes))
    Should Not Be Empty    ${novos}
    Switch Window    ${novos}[0]
Valida conteúdo da nova aba com o titulo "${titulo_pagina_inicial}"
    Page Should Contain    ${titulo_pagina_inicial}
Retorna para aba original
    Close Window
    Switch Window    ${antes}[0]
    Wait Until Element Is Visible    ${titulo_pagina_inicial_demoqa}    timeout=10s
Abre nova janela via "New Window"
    Click Button    ${btnnewwindow}
Gerencia múltiplas janelas simultaneamente
    ${todas}=    Get Window Handles
    ${qtde}=    Get Length    ${todas}
    Should Be True    ${qtde} > 1