*** Settings ***
Resource    ../main/main.robot

*** Keywords ***
Gerar csv dinamico
    [Arguments]    ${qtd}
    ${arquivo}=    Generate    ../fixture/valido_${qtd}.csv    ${qtd}
    Log    CSV gerado em: ${arquivo}
    File Should Exist    ${arquivo}
Realizar o upload do arquivo valido "${nomecsv}"
    ${arquivo}=    Set Variable   ${variable_fixture}\\${nomecsv}.csv 
    Choose File    ${btnescolherarquivo}    ${arquivo} 

Realizar o upload do arquivo csv "${tipodecsv}"
    IF    "${tipodecsv}" == "vazio"
        Realizar o upload do arquivo csv vazio
    ELSE IF    "${tipodecsv}" == "formato inválido"
        Realizar o upload do arquivo csv com formato inválido
    ELSE IF    "${tipodecsv}" == "dados malformados"
        Realizar o upload do arquivo csv com dados malformados
    END
Validar upload do arquivo bem sucedido
    Realizar o upload do arquivo csv vazio
    Click Button    ${btnupload}
    Wait Until Element Is Visible    ${mensagem_sucesso}    timeout=10s

Realizar o upload do arquivo csv vazio
    ${arquivo}=    Normalize Path    ../fixture/vazio.csv
    Create File    ${arquivo}    ${EMPTY}    encoding=UTF-8
    ${arquivo}=    Set Variable    ${variable_fixture}\\vazio.csv 
    Choose File    ${btnescolherarquivo}    ${arquivo} 
Realizar o upload do arquivo csv com formato inválido
    ${arquivo}=    Normalize Path    ../fixture/invalido.txt
    Create File    ${arquivo}    Este arquivo não é um CSV    encoding=UTF-8
    ${arquivo}=    Set Variable    ${variable_fixture}\\invalido.txt 
    Choose File    ${btnescolherarquivo}    ${arquivo} 
Realizar o upload do arquivo csv com dados malformados
    ${arquivo}=    Normalize Path    ../fixture/invalido.txt
    Create File    ${arquivo}    Coluna1,Coluna2,\nColuna3Valor1,Valor2,Valor3    encoding=UTF-8
    ${arquivo}=    Set Variable    ${variable_fixture}\\invalido.txt 
    Choose File    ${btnescolherarquivo}    ${arquivo} 

