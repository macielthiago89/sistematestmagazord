*** Settings ***
Resource    ../main/main.robot
*** Test Cases ***
5.1test
    [Documentation]    Exemplo genérico: abre o app, interage com 1 elemento e valida outro.
    ...    Ajuste capabilities e locators conforme o app escolhido.
    [Tags]    regression    5.1test    MOBILEMAGAZORD
    ${caps}=    Create Dictionary
    ...    platformName=${platform}
    ...    automationName=UiAutomator2
    ...    deviceName=${device_name}
    ...    app=${app_path}
    ...    newCommandTimeout=120

    Open Application    ${appim_url}    &{caps}

    # --- EXEMPLO DE AÇÕES ---
    # Substitua os locators abaixo pelos do seu app
    # Click Element    accessibility_id=Login
    # Wait Until Page Contains Element    accessibility_id=Home    10

    # Verificação genérica (apenas para não ficar vazio)
    Log    App aberto com sucesso. Ajuste locators para seu app.

    Close Application
