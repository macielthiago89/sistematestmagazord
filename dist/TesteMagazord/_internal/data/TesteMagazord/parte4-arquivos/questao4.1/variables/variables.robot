*** Variables ***

# Test Setup
${site}    https://the-internet.herokuapp.com/upload
${titulo_pagina_inicial}    //h3[contains(normalize-space(.),"File Uploader")]

# Tests
${btnescolherarquivo}    //input[@id="file-upload"]
${btnupload}    //input[@id="file-submit"]
${mensagem_sucesso}    //h3[normalize-space(text())="File Uploaded!"]
${path_fixture}    ${EXECDIR}\\fixture\\