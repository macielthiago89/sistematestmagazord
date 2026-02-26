*** Settings ***

Resource    ../main/main.robot

*** Keywords ***
Criar sessao GitHub
    Create Session    ${sessao}   ${base_url}    verify=${True}
Fazer GET usuario GitHub
    ${resp}=    GET On Session    ${sessao}    ${endpoint}
    RETURN    ${resp}
Rate limit guard
    [Arguments]    ${resp}
    ${remaining}=   Get From Dictionary    ${resp.headers}    X-RateLimit-Remaining
    ${reset}=       Get From Dictionary    ${resp.headers}    X-RateLimit-Reset
    ${remaining}=   Convert To Integer    ${remaining}
    ${reset}=       Convert To Integer    ${reset}

    IF    ${remaining} <= ${THRESHOLD}
        ${now}=        Get Current Date    result_format=epoch
        ${wait_ms}=    Evaluate    max(0, (${reset}*1000) - (${now}*1000) + ${SAFETY_MS})
        Log    [Guard] remaining=${remaining} -> esperando ${wait_ms} ms até o reset
        Sleep    ${wait_ms}ms
    ELSE
        Log    [Guard] remaining=${remaining} ok
    END

Validar headers rate limit
    Criar sessao GitHub
    ${resp}=    Fazer GET usuario GitHub
    Should Be Equal As Integers    ${resp.status_code}    200

    Dictionary Should Contain Key    ${resp.headers}    X-RateLimit-Limit
    Dictionary Should Contain Key    ${resp.headers}    X-RateLimit-Remaining
    Dictionary Should Contain Key    ${resp.headers}    X-RateLimit-Reset

    ${limit}=       Get From Dictionary    ${resp.headers}    X-RateLimit-Limit
    ${remaining}=   Get From Dictionary    ${resp.headers}    X-RateLimit-Remaining
    ${reset}=       Get From Dictionary    ${resp.headers}    X-RateLimit-Reset

    ${limit}=      Convert To Integer    ${limit}
    ${remaining}=  Convert To Integer    ${remaining}
    ${reset}=      Convert To Integer    ${reset}

    Should Be True    ${limit} > 0
    Should Be True    ${remaining} >= 0
    Should Be True    ${reset} > 0

    Log    RateLimit: limit=${limit} remaining=${remaining} reset=${reset}

Nao bloquear testes
    Criar sessao GitHub
    ${resp1}=    Fazer GET usuario GitHub
    Rate limit guard    ${resp1}

    ${resp2}=    Fazer GET usuario GitHub
    Should Be True    ${resp2.status_code} in [200, 403]

Detectar rate limit atingido
    Criar sessao GitHub
    ${resp}=    Fazer GET usuario GitHub

    IF    ${resp.status_code} == 403
        Log    Rate limit atingido (403) detectado.

        Should Contain    ${resp.text}    rate limit
    ELSE
        Log    Ainda com cota (status=${resp.status_code}). Teste detecta 403 quando ocorrer.
        Should Be Equal As Integers    ${resp.status_code}    200
    END

Criar sessao Reqres
    Create Session    ${sessao}   ${base_url2}    verify=${True}

Autenticação que obtém token via POST /api/login
    Criar sessao Reqres
    &{body}=    Create Dictionary    email=${email}    password=${password}
    ${resp}=    POST On Session    ${sessao}    ${login_ep}    json=${body}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${json}=    Evaluate    ${resp.json()}
    ${token}=   Get From Dictionary    ${json}    token
    Log    Token obtido: ${token}
    Should Not Be Empty    ${token}