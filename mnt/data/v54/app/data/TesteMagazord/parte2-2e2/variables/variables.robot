*** Variables ***

# Test Setup
${sitesaucedemo}    https://www.saucedemo.com/
${username}    standard_user    #Username do usuario
${password}    secret_sauce     #Password do usuario
${titulo_pagina_inicial_saucedmo}    //div[contains(normalize-space(.),"Swag Labs")]
${campousuario}   //input[contains(@id,'user-name')] 
${campopassword}   //input[contains(@id,'password')]
${btn_login}        //input[contains(@id,'login-button')] 
${titulo_produtos}    //span[@class='title'][contains(.,'Products')]
${imagem_carrinho}    //a[contains(@class,'shopping_cart_link')]

${produtoSauceLabsBackpack}    //button[@id="add-to-cart-sauce-labs-backpack"]
${titulocarrinho}    //span[normalize-space(text())="Your Cart"]
${produtoSauceLabsBackpackcarrinho}    //div[normalize-space(text())="Sauce Labs Backpack"]
${btn_checkout}    //button[@id="checkout"]
${titulocheckout}    //span[contains(normalize-space(.),"Checkout: Overview")]
${btnfinish}    //button[@id="finish"]
${campofirstname}    //input[@id="first-name"]
${campolastname}    //input[@id="last-name"]
${campopostalcode}    //input[@id="postal-code"]
${btncontinue}    //input[@id="continue"]
${textsucessocheckout}    //h2[normalize-space(text())="$$"]
${sitedemoqa}    https://demoqa.com/browser-windows
${titulo_pagina_inicial_demoqa}    //h1[contains(normalize-space(.),"Browser Windows")]
${btnnewtab}    //button[normalize-space(text())="New Tab"]
${btnnewwindow}    //button[normalize-space(text())="New Window"]