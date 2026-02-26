*** Variables ***

# Test Setup
${site}    https://demoqa.com/automation-practice-form
${titulo_pagina_inicial}    //h1[contains(normalize-space(.),"Practice Form")]

# Tests
${campoemail}          xpath=//input[@id="userEmail"]
${campoemailinvalido}  css=#userEmail:invalid
${campoemailvalido}  css=#userEmail:valid
${btnsubimit}    //button[@type="submit"]
${campotelefone}    xpath=//input[@id="userNumber"]
${campotelefoneinvalido}  css=#userNumber:invalid
${campotelefonevalido}  css=#userNumber:valid
${campofirstname}    xpath=//input[@id="firstName"]
${campolastname}    xpath=//input[@id="lastName"]
${campodateofbirth}    css=#dateOfBirthInput
${radiogender}    xpath=//label[contains(normalize-space(.),"$$")]
${camposubjects}    css=#subjectsInput
${checkboxhobbies}    xpath=//label[contains(normalize-space(.),"$$")]
${checkboxhobbiescss}    css=#hobbies-checkbox-$$
${btnescolherarquivo}    xpath=//input[@id="uploadPicture"]
${campoaddress}    xpath=//textarea[@id="currentAddress"]
${variaveladdress}    css=#currentAddress
${campostate}    xpath=//input[@id="react-select-3-input"]
${variavelstate}    css=#react-select-3-input
${campocity}    xpath=//input[@id="react-select-4-input"]
${variavelcity}    css=#react-select-4-input
${mensagemconfirmacao}    xpath=//div[contains(@class,'modal-content')]
${closemodal}    xpath=//button[@id="closeLargeModal"]
${modalbackdrop}    css=.modal-backdrop
${modalshow}    css=.modal.show
${modal}    xpath=//div[contains(@class,'modal-content')]