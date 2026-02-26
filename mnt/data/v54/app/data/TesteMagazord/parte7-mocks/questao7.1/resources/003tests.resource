*** Settings ***
Resource    ../main/main.robot

*** Keywords ***
GET /products - sucesso + schema
    Reset Mock State
    ${resp}=    GET On Session    mock    /products
    Should Be Equal As Integers    ${resp.status_code}    200
    ${items}=    Set Variable    ${resp.json()}
    ${qtd}=      Get Length      ${items}
    Should Be True    ${qtd} >= 1
    Validate Product Schema    ${items}[0]    ${SCHEMA}

POST /products - criar produto
    Reset Mock State
    &{payload}=    Create Dictionary    title=New Product    price=123.45    description=abc    category=mock    image=https://example.com/x.png
    ${resp}=    POST On Session    mock    /products    json=${payload}
    Should Be Equal As Integers    ${resp.status_code}    201
    ${obj}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${obj}    id
    Should Be Equal    ${obj}[title]    New Product
    Validate Product Schema    ${obj}    ${SCHEMA}

PUT /products/:id - atualizar produto
    Reset Mock State
    &{payload}=    Create Dictionary    title=Updated    price=77.7
    ${resp}=    PUT On Session    mock    /products/1    json=${payload}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${obj}=    Set Variable    ${resp.json()}
    Should Be Equal As Integers    ${obj}[id]    1
    Should Be Equal    ${obj}[title]    Updated
    Validate Product Schema    ${obj}    ${SCHEMA}

DELETE /products/:id - deletar produto
    Reset Mock State
    ${resp}=    DELETE On Session    mock    /products/2
    Should Be Equal As Integers    ${resp.status_code}    200
    ${obj}=    Set Variable    ${resp.json()}
    Should Be True    ${obj}[deleted]

Erro 500 simulado
    Reset Mock State
    &{params}=    Create Dictionary    error=500
    ${resp}=    GET On Session    mock    /products    params=${params}    expected_status=ANY
    Should Be Equal As Integers    ${resp.status_code}    500
    Should Contain    ${resp.text}    internal

Rate limit simulado (429 após 10 GETs)
    Reset Mock State
    FOR    ${i}    IN RANGE    1    13
        ${resp}=    GET On Session    mock    /products    expected_status=ANY
        IF    ${i} <= 10
            Should Be Equal As Integers    ${resp.status_code}    200
        ELSE
            Should Be Equal As Integers    ${resp.status_code}    429
            Should Contain    ${resp.text}    Rate limit
        END
    END