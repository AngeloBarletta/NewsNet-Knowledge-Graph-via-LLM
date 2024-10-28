#Questo script è utile a verificare che tutte le relazioni trovate in precedenza dal modello sono effettivamente possibili
#Esempio: il modello potrebbe trovare una relazione di tipo leader_of tra due entità di tipo organization, questo non è valido. Le possibili combinazioni sono state definite all'interno del file 'relazioni_consentite.csv'
import pandas as pd

#Lettura dei dataframe dai file .csv creati nel main.py relativi a relazioni e entità
df_relations = pd.read_csv("unique_relations.csv")
df_entities = pd.read_csv("unique_entities.csv")
#dataframe all'interno del quale sono contenute le relazioni consentite
df_relazioni_consentite = pd.read_csv("relazioni_consentite.csv")

#Definizione di un dataframe che conterrà le relazioni filtrate
df_final_relations = pd.DataFrame(columns = ['Relation','Source','Target'])

num_relazioni_eliminate = 0

#Iterazioni su tutti gli elementi del dataframe delle relazioni
for index, riga in df_relations.iterrows():
    relation = riga['Relation']
    source = riga['Source']
    target = riga['Target']

    source_types = []
    target_types = []

    #Per ogni relazione verifichiamo se le entità source e target esistono e ne recuperiamo i tipi (possono essere più di uno come: Giorgia Meloni = Person e Politician)
    for index2,riga2 in df_entities.iterrows():
        if (riga2['Name'] == source):
            source_types.append(riga2['Type'])

        if (riga2['Name'] == target):
            target_types.append(riga2['Type'])    

    #In quest'altro ciclo verifichiamo se la relazione tra source e target è consentita 
    #Se sì viene mantenuta, altrimenti viene eliminata
    mantieni = False
    for index3,riga3 in df_relazioni_consentite[df_relazioni_consentite['Relazione'] == relation].iterrows():
        if (riga3['Tipo1'] in source_types) and (riga3['Tipo2'] in target_types):
            mantieni = True
            df_final_relations = df_final_relations._append({'Relation':relation, 'Source':source, 'Target':target}, ignore_index = True)
            break
    
    if mantieni == False:
        num_relazioni_eliminate +=1
        #Debug: verifico quali relazioni vengono eliminate
        print(str(relation) + " " + str(source) + "("+ str(source_types) +")" + " " + str(target) + "("+ str(target_types) +")" + " ---- " + str(num_relazioni_eliminate))
        
    

print("\n RELAZIONI ELIMINATE: " + str(num_relazioni_eliminate) + "\n\n")
print(df_final_relations.head())

#Scrittura del dataframe filtrato nel file final_unique_relations.csv
df_final_relations.to_csv("final_unique_relations.csv", index = False)
