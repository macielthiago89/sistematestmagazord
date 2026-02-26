*** Settings ***

Resource    ../main/main.robot

*** Keywords ***
Test teardown
    [Arguments]    ${EVIDENCIA}    ${CASODETESTE}
    Capture Page Screenshot    ${EVIDENCIA}-${CASODETESTE}.png    #Sistema captura a tela e renomea com o nome da tela e o numero do caso de teste
    Set Window Size    1920    1080
    Delete All Cookies
    Close Browser    #Fecha o navegador