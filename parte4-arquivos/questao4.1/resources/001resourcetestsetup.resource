*** Settings ***
Resource    ../main/main.robot

*** Keywords ***
Test Setup
    Acessar o site "the-internet"

Acessar o site "${titulosite}"    # keyword resonsavel por abrir o browser e acessar o site do swag labs
    Open Browser    url=${site}    browser=headlesschrome
    Set Window Size    1920    1080
    Maximize Browser Window
    Wait Until Element Is Visible    ${titulo_pagina_inicial}    timeout=10s