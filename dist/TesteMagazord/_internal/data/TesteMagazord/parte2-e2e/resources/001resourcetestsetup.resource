*** Settings ***
Resource    ../main/main.robot

*** Keywords ***
Test Setup Swag Labs
    Acessar o site "Swag Labs"
    Inserir no campo username o username do usuario  
    Inserir no campo password a senha do usuario
    Clique em login
    Verificar o login no site "Swag Labs"
Test Setup Demoqa
    Acessar o site "DemoQa"
Acessar o site "${titulosite}"    # keyword resonsavel por abrir o browser e acessar o site do swag labs
    IF    "${titulosite}" == "Swag Labs" 
        Open Browser    url=${sitesaucedemo}    browser=headlesschrome
        Set Window Size    1920    1080
        Maximize Browser Window
        Wait Until Element Is Visible    ${titulo_pagina_inicial_saucedmo}    timeout=10s
    ELSE IF    "${titulosite}" == "DemoQa"
        Open Browser    url=${sitedemoqa}    browser=headlesschrome
        Set Window Size    1920    1080
        Maximize Browser Window
        Wait Until Element Is Visible    ${titulo_pagina_inicial_demoqa}    timeout=10s
    END
    
Inserir no campo username o username do usuario     # Keyword responsavel por inserir o username do usuario
    Click Element    ${campousuario}
    Input Text    ${campousuario}    ${username}
Inserir no campo password a senha do usuario     # Keyword responsavel por inserir o password do usuario
    Click Element    ${campopassword}
    Input Text    ${campopassword}    ${password}    
Clique em login    # Keyword responsavel por clicar no botão de login
    Click Element    ${btn_login}
Verificar o login no site "${site}"    # Keyword responsavel por verificar o sucesso no login
    Wait Until Element Is Visible    ${titulo_produtos}     timeout=10s
    Wait Until Element Is Visible    ${imagem_carrinho}    timeout=10s


