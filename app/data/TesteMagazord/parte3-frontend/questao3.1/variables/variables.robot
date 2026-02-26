*** Variables ***

# Test Setup
${site}    https://the-internet.herokuapp.com/dynamic_content
${titulo_pagina_inicial}    //h3[contains(normalize-space(.),"Dynamic Content")]

# Tests
${css_selector}    css=#content
${texto_visivel}    xpath=//a[normalize-space(.)='click here']
${estrutura_dom}    css=#content .row:nth-child(1) .large-10
${atributo_parcial}    css=#content img[src*="avatar"]
${hierarquia}    css=#content .row:nth-child(1) > div.large-10
${xpath}    xpath=//*[@id='content']//div[contains(@class,'row')][3]//div[contains(@class,'large-10')]   