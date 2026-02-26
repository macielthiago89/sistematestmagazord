*** Settings ***

Resource    ../main/main.robot

*** Keywords ***
Verificar por "${valor}"
    FOR    ${i}    IN RANGE    1    6
        Wait Until Page Contains Element    ${css_selector}    10s
        IF    "${valor}" == "texto visível"
            Page Should Contain Element    ${texto_visivel}
        ELSE IF    "${valor}" == "estrutura DOM (nth-child)"
            ${t1}=    Get Text    ${estrutura_dom}
            Should Not Be Empty    ${t1}
        ELSE IF    "${valor}" == "atributo parcial"
            ${atributo}    Get Element Attribute    ${atributo_parcial}    src
            Should Contain    ${atributo}    avatar
        ELSE IF    "${valor}" == "hierarquia (parent > child)"  
            ${t2}=    Get Text    ${hierarquia}
            Should Not Be Empty    ${t2}
        ELSE IF    "${valor}" == "XPath"  
            ${t3}=    Get Text    ${xpath}
            Should Not Be Empty    ${t3}
        END
        Reload Page
    END