*** Settings ***
Resource    ../main/main.robot

*** Keywords ***
Test Setup
    Acessar o site "theinternet"    # keyword resonsavel por abrir o browser e acessar o site do swag labs

Acessar o site "${titulosite}"    # keyword resonsavel por abrir o browser e acessar o site do swag labs
    Open Browser    url=${site}    browser=headlesschrome
    Maximize Browser Window
    Wait Until Element Is Visible    ${titulo_pagina_inicial}    timeout=10s