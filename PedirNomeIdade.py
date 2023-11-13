from PyTME import *
x=Pytme()
x.text("Digite seu nome: ");
nome=x.type_text();
x.text_ln();
x.text("Digite sua idade: ");
idade=int( x.type_text() );
x.text_ln();
x.text_ln("Pressione <ENTER>");
x.type_text();
x.clr_scr();  # apaga a tela após o usuário pressionar <ENTER>
x.text("Seu nome eh ");
x.text(nome);
x.text(" e voce tem ");
x.text(idade);
x.text(" anos!");
x.type_text();