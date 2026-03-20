arquivo = open('arqText.txt', 'w')

arquivo.write('Curso Python\n')
arquivo.write('Aula Prática')
arquivo.close()

#leitura do arquivo texto

leitura=open('arqText.txt', 'r')
print(leitura.read())
leitura.close()