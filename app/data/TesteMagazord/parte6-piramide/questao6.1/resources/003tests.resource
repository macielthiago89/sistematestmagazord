*** Settings ***

Resource    ../main/main.robot
Library    OperatingSystem

*** Keywords ***
Inserir um email invalido no campo de email
    Gerar nome aleatório
    Click Element    ${campoemail}
    Input Text    ${campoemail}    ${nome}
    Clicar no botao submit
    Page Should Contain Element    ${campoemailinvalido}

Inserir um email valido no campo de email
    Gerar email aleatório
    Click Element    ${campoemail}
    Input Text    ${campoemail}    ${email}
    Clicar no botao submit
    Page Should Contain Element    ${campoemailvalido}
Inserir um telefone invalido no campo de telefone
    Gerar nome aleatório
    Click Element    ${campotelefone}
    Input Text    ${campotelefone}    ${nome}
    Clicar no botao submit
    Page Should Contain Element    ${campotelefoneinvalido} 
Inserir um telefone valido no campo de telefone
    Gerar "10" numero aleatorios
    Click Element    ${campotelefone}
    Input Text    ${campotelefone}    ${numero}
    Clicar no botao submit
    ${valido}=    Execute JavaScript    return document.querySelector('#userNumber').checkValidity();
    Should Be True    ${valido}
Validar a data valida
    ${datasistema}=    Get Value    ${campodateofbirth}
    ${data}=          Data atual no formato ddMmmYYYY
    Should Be Equal    ${datasistema}    ${data}

Clicar no botao submit
    Wait Until Element Is Visible    ${btnsubimit}    10s
    Scroll Element Into View         ${btnsubimit}
    Execute JavaScript    window.scrollBy(0, -250);
    Sleep    150ms
    Run Keyword And Ignore Error    Click Element    ${btnsubimit}
    ${result}=    Run Keyword And Return Status    Page Should Contain Element    ${modal}
    IF    not ${result}
        ${el}=    Get WebElement    ${btnsubimit}
        Execute JavaScript    arguments[0].click();    ARGUMENTS    ${el}
    END

Clicar no campo data de aniversario
    Wait Until Element Is Visible    ${campodateofbirth}    10s
    Scroll Element Into View         ${campodateofbirth}
    Execute JavaScript    window.scrollBy(0, -250);
    Sleep    150ms
    Run Keyword And Ignore Error    Click Element    ${campodateofbirth}
    ${result}=    Run Keyword And Return Status    Page Should Contain Element    ${modal}
    IF    not ${result}
        ${el}=    Get WebElement    ${campodateofbirth}
        Execute JavaScript    arguments[0].click();    ARGUMENTS    ${el}
    END

Preencher o campo "First Name" com um nome aleatório
    Gerar nome aleatório
    Click Element    ${campofirstname}
    Input Text    ${campofirstname}    ${nome}
Preencher o campo "Last Name" com um sobrenome aleatório
    Gerar sobrenome aleatório
    Click Element    ${campolastname}
    Input Text    ${campolastname}    ${sobrenome}
Selecione o Gender como "${valor}"
    ${varialvelgender}    Replace String    ${radiogender}    $$     ${valor}
    Click Element    ${varialvelgender}
Preencha a data de nascimento com "${valor}"
    Clicar no campo data de aniversario
    Input Text    ${campodateofbirth}    ${valor}
Selecionar subject "${valor}"
    Fechar modal do site
    Scroll Element Into View         ${camposubjects}
    Wait Until Element Is Visible    ${camposubjects}    10s
    Execute JavaScript    document.querySelector('#subjectsInput').focus();
    Input Text            ${camposubjects}    ${valor}
    Press Keys            ${camposubjects}    ENTER
Selecionar hobbies "${valor}"
    ${varialvelcheckboxhobbiescss}    Replace String    ${checkboxhobbiescss}    $$     ${valor}
    Fechar modal do site
    Wait Until Element Is Visible    ${varialvelcheckboxhobbiescss}    10s
    Scroll Element Into View         ${varialvelcheckboxhobbiescss}
    Execute JavaScript    window.scrollBy(0, -250);
    Sleep    150ms
    Run Keyword And Ignore Error    Click Element    ${varialvelcheckboxhobbiescss}
    ${result}=    Run Keyword And Return Status    Page Should Contain Element    ${modal}
    IF    not ${result}
        ${el}=    Get WebElement    ${varialvelcheckboxhobbiescss}
        Execute JavaScript    arguments[0].click();    ARGUMENTS    ${el}
    END
    Press Keys            ${varialvelcheckboxhobbiescss}    ENTER
Faça upload de um arquivo de imagem
    ${caminho}=    Normalize Path    ${CURDIR}/imagem.png
    File Should Exist    ${caminho}
    Choose File    ${btnescolherarquivo}    ${caminho}
Preencher o campo "Current Address" com um endereço aleatório
    Fechar modal do site
    Wait Until Element Is Visible    ${variaveladdress}    10s
    Scroll Element Into View         ${variaveladdress}
    Execute JavaScript    window.scrollBy(0, -250);
    Sleep    150ms
    Run Keyword And Ignore Error    Click Element    ${variaveladdress}
    ${result}=    Run Keyword And Return Status    Page Should Contain Element    ${modal}
    IF    not ${result}
        ${el}=    Get WebElement    ${variaveladdress}
        Execute JavaScript    arguments[0].click();    ARGUMENTS    ${el}
    END
    Gerar endereço aleatório
    # Click Element    ${campoaddress}
    Input Text    ${campoaddress}    ${endereco}
    
Selecione o estado "${state}"
    Fechar modal do site
    Wait Until Element Is Visible    ${variavelstate}    10s
    Scroll Element Into View         ${variavelstate}
    Execute JavaScript    window.scrollBy(0, -250);
    Sleep    150ms
    Run Keyword And Ignore Error    Click Element    ${variavelstate}
    ${result}=    Run Keyword And Return Status    Page Should Contain Element    ${modal}
    IF    not ${result}
        ${el}=    Get WebElement    ${variavelstate}
        Execute JavaScript    arguments[0].click();    ARGUMENTS    ${el}
    END
    # Click Element    ${campostate}
    Input Text    ${campostate}    ${state}


Selecione a cidade "${city}"
    Fechar modal do site
    Wait Until Element Is Visible    ${variavelcity}    10s
    Scroll Element Into View         ${variavelcity}
    Execute JavaScript    window.scrollBy(0, -250);
    Sleep    150ms
    Run Keyword And Ignore Error    Click Element    ${variavelcity}
    ${result}=    Run Keyword And Return Status    Page Should Contain Element    ${modal}
    IF    not ${result}
        ${el}=    Get WebElement    ${variavelcity}
        Execute JavaScript    arguments[0].click();    ARGUMENTS    ${el}
    END
    # Click Element    ${campocity}
    Input Text    ${campocity}    ${city}

Validar que o modal de confirmação foi exibido
    Page Should Contain Element    ${mensagemconfirmacao}

Fechar modal do site
    ${aberto}=    Run Keyword And Return Status    Page Should Contain Element    ${modalshow}
    IF    not ${aberto}
        RETURN
    END
    Run Keyword And Ignore Error    Click Button    ${closemodal}
    Run Keyword And Ignore Error    Click Button    ${closemodal}
    Press Keys    css=body    ESC
    Run Keyword And Ignore Error    Click Element    ${modalbackdrop} 
    Wait Until Page Does Not Contain Element    ${modalshow}    15s
    Run Keyword And Ignore Error    Wait Until Page Does Not Contain Element    ${modalbackdrop}    15s





