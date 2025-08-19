import smtplib

server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.login('ton.email@gmail.com', 'mot_de_passe_app')
server.quit()
print("Connexion SMTP réussie !")
    