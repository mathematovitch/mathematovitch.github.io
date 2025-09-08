import random

def exo(nombre):
  for i in range(nombre):
  
      def random_var(var1, var2):
        r = random.random()
        if r < 0.5:
          return (var1, var2)
        else:
          return (var2, var1)
          
      def rand_int():
      
        m = random.randint(1, 9)
        c = random.randint(1, 9)
        d = random.randint(1, 4)
        u = random.randint(3, 15)
        
        unite = str(u)
        dizaine = str(d) + unite
        centaine = str(c) + dizaine
        milliers = str(m) + ' ' + centaine
        
        liste_entier = [unite]
        
        return random.choice(liste_entier)
      
      
      def rand_float():
        
        dd = random.randint(1, 9)
        cc = random.randint(1, 9)
        mm = random.randint(1, 9)
        
        dixieme = rand_int() + ',' + str(dd)
        centieme = rand_int() + ',' + str(dd) + str(cc)
        millieme = rand_int() + ',' + str(dd) + str(cc) + str(mm)
        
        liste_decimaux = [dixieme,centieme,millieme]
        
        return random.choice(liste_decimaux)
      
      def random_power():
          r = random.random()
          if r < 0.33:
              return str('10')
          elif r < 0.66:
              return str('100')
          else:
              return str('1 000')
              
      def random_pow():
      	liste_puissance = ['10','100','1 000']
      	return random.choice(liste_puissance)
              
      def random_dec():
      	liste_decimaux = ['0,1','0,01']
      	return random.choice(liste_decimaux)
      	
      coeff = int(rand_int())
      n1 = int(rand_int())
      n2 = int(rand_int())
      n3 = int(rand_int())
      n4 = int(rand_int())
      
      m1 = coeff*n1
      m2 = coeff*n2
      m3 = coeff*n3
      m4 = coeff*n4
          
      print("""
\\begin{tabular}{|l|c|c|c|c|}
\\hline
Quantité A & %d & %d & %d & %d  \\\ \\hline
Quantité B & %d & %d & %d & %d \\\ \\hline
\\end{tabular}
"""

%  (n1,n2,n3,n4,m1,m2,m3,m4))
        
exo(1)   
