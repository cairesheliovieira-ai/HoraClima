notaA=float(input("informe um valor para a nota A: "))
notaB=float(input("informe um valor para a nota B: "))

#calcular media
mediafinal = (notaA + notaB) / 2

#verificação
if mediafinal >=7.0:
    print("A Média: %.1f - Aprovado"% mediafinal)
else:
    print("A Média: %.1f - Reprovado " %mediafinal)