from typing import Callable

from Artifact import *
from Build import *

import numpy as np
import pandas as pd

from codetiming import Timer




# Cria as builds (indivíduos) da população 
def create_population(database: list[Artifact], pop_size: int) -> tuple[list[Build], dict[str, np.ndarray]]:

    # database -> 300 artefatos de cada tipo, 1500 (300 * 5) no total

    # Separa a base de dados por artefato 
    flowers  = np.array(list(filter(lambda a: a.type_ == 'Flower',  database)))
    feathers = np.array(list(filter(lambda a: a.type_ == 'Feather', database)))
    sands    = np.array(list(filter(lambda a: a.type_ == 'Sand',    database)))
    goblets  = np.array(list(filter(lambda a: a.type_ == 'Goblet',  database)))
    circlets = np.array(list(filter(lambda a: a.type_ == 'Circlet', database)))

    flowers = np.random.choice(flowers, pop_size, replace=False)
    feathers = np.random.choice(feathers, pop_size, replace=False)
    sands = np.random.choice(sands, pop_size, replace=False)
    goblets = np.random.choice(goblets, pop_size, replace=False)
    circlets = np.random.choice(circlets, pop_size, replace=False)

    builds = np.array([])
    for i in np.arange(pop_size):
        b = Build(flowers[i], feathers[i], sands[i], goblets[i], circlets[i])
        builds = np.append(builds, b, axis = None)

    bag_of ={
        "flower": flowers,
        "feather": feathers,
        "sand": sands,
        "goblet": goblets,
        "circlet": circlets,
    }

    return builds, bag_of



def fitness_1(build: Build) -> float:

    sheet = build.get_artifact_sheet()

    ##############

    # Weapon_Crit_DMG = 66.2
    # Char_Crit_DMG = 38.4
    # Char_Base_ATK = 106.51
    # Weapon_Base_ATK = 608
    # Base_ATK = Weapon_Base_ATK + Char_Base_ATK
    # Weapon_Passive_1_HP = 20.0
    # Char_HP = 15552
    Total_HP = 15552 * np.divide(120.0 + sheet["HP%"], 100.0) + sheet["HP"]
    Elemental_Skill_ATK = np.min([np.multiply(0.06256, Total_HP), 2858.04]) # facade coeficient = 0.063 ; true coeficient = 0.06256
    Total_Weapon_Passive_ATK = np.divide(1.8 * Total_HP, 100.0)
    # Enemy_Pyro_Res = 10
    # Enemy_Level = 90
    # Char_Level = 90
    # Enemy_DEF_Multiplier = 0.5 # (Char._Level + 100)/(Char._Level + 100 + Enemy_Level + 100)
    # Active_Talent_Passive = 33.0
    # Artifact_Active_Set_Bonus = 22.5 # = 15% (2-piece bonus) + 7.5 (4-piece bonus)
    # Total_Pyro_DMG_Bonus = 33.0 + Active_Set_Bonus + sheet["Pyro"]
    Total_DMG_Bonus = np.divide(55.5 + sheet["Pyro"], 100.0)

    ##############

    Total_Crit_DMG = np.divide(154.6 + sheet["CD"], 100.0)

    Total_Crit_Rate = np.divide(np.min([5.0 + sheet["CR"], 100]), 100.0)

    Total_ATK = Elemental_Skill_ATK + Total_Weapon_Passive_ATK + np.multiply(714.51, np.divide(100 + sheet["ATK%"], 100.0)) + sheet["ATK"]

    ##############

    return np.multiply(np.multiply(np.multiply(np.multiply(2.4255, Total_ATK), 1 + np.multiply(Total_Crit_Rate, Total_Crit_DMG)), 1 + Total_DMG_Bonus), 0.45) # facade coeficient = 2.426 ; true coeficient = 2.4255



def fitness_2(build: Build) -> float:

    sheet = build.get_artifact_sheet()

    # Weapon_Passive = 46.9
    # Char_HP = 14695

    # Total_Shield_Strength = 0.25 # + Artifacts
    Total_HP = 14695 * np.divide(146.9 + sheet["HP%"], 100.0) + sheet["HP"]

    return np.multiply(1.875, (0.23*Total_HP + 2711.5))
    


# N-point crossover -> Escolhe N pontos de corte e gera 2 novos indivíduos
def crossover(b1: Build, b2: Build, points: int = 2) -> tuple[Build, Build]:

    # Link que ajuda a entender o código
    # https://medium.com/@samiran.bera/crossover-operator-the-heart-of-genetic-algorithm-6c0fdcb405c0

    possible_cuts = [0, 1, 2, 3, 4]
    random_cut = np.random.choice(possible_cuts, size = points, replace = False)

    #           <--0         <--1           <--2        <--3          <--4
    cromossome_1 = [b1["flower"], b1["feather"], b1["sand"], b1["goblet"], b1["circlet"]]
    cromossome_2 = [b2["flower"], b2["feather"], b2["sand"], b2["goblet"], b2["circlet"]]

    for cut in np.sort(random_cut):
        temp = cromossome_1[:cut] + cromossome_2[cut:]
        cromossome_2 = cromossome_2[:cut] + cromossome_1[cut:]
        cromossome_1 = temp

    b1 = Build(cromossome_1[0], cromossome_1[1],cromossome_1[2],cromossome_1[3],cromossome_1[4])
    b2 = Build(cromossome_2[0], cromossome_2[1],cromossome_2[2],cromossome_2[3],cromossome_2[4])

    return (b1, b2)



# Reset mutation -> Substitui um gene por outro gerado aleatoriamente
def mutation(b: Build, bag_of: dict[str, np.ndarray], useless_substats: list[str]) -> Build:

    genes_types = ["flower", "feather", "sand", "goblet", "circlet"]

    for gene_type in genes_types:

        new_artifact = b[gene_type]

        useless_stat_count = 3
        while useless_stat_count > 2:
            new_artifact = np.random.choice(bag_of[gene_type], size = 1, replace = False)[0]
            useless_stat_count = new_artifact.count_useless_substats(useless_substats)

        # b[random_type] = new_artifact
        b[gene_type] = new_artifact

    return b

    ### Versões anteriores da fução de mutação ###
    # for gene_type in genes_types:
    #     useless_stat_count = b[gene_type].count_useless_substats(useless_substats)
    #     new_artifact = b[gene_type]

    #     # Tenta escolher um artefato que contrubui significativamente para a build
    #     while useless_stat_count > 2:
    #         new_artifact = np.random.choice(bag_of[gene_type], size = 1, replace = False)[0]
    #         useless_stat_count = new_artifact.count_useless_substats(useless_substats)

    #     # b[random_type] = new_artifact
    #     b[gene_type] = new_artifact

    # random_type = np.random.choice(genes_types, size = 1, replace = False)[0]
    # artifacts = bag_of[random_type]

    # useless_stat_count = 3
    # while useless_stat_count > 2:
    #     new_artifact = np.random.choice(artifacts, size = 1, replace = False)[0]
    #     useless_stat_count = new_artifact.count_useless_substats(useless_substats)

    # b[gene_type] = new_artifact
    #############################################

"""
fitness -> Função fitness que será usada
target_fitness -> Um dos objetivos de parada
useless -> Lista de substats que não contribuem para a build
"""
@Timer(name="decorator", text="Tempo da busca: {:.4f} segundos")
def GA(fitness: Callable, 
       target_fitness: int, 
       useless: list[str], 
       seed: int):

    # Parâmetros
    RANDOM_SEED = seed
    POP_SIZE = 300
    MAX_GENERATIONS = 10000
    MAX_NO_CHANGE_GENERATIONS = 750
    CROSSOVER_RATE = 0.75
    MUTATION_RATE = 0.50
    N_POINT = 3 # N-point crossover

    # Configuração inicial
    np.random.seed(seed=RANDOM_SEED)
    artifacts = Artifact.read_database()
    population, bag_of_artifacts = create_population(artifacts, POP_SIZE)

    generation_fitness = np.zeros(shape=[POP_SIZE])
    best_fitness: float = -np.inf
    best_individual: Build = None
    best_index: int = None

    # Calcula o fitness da geração atual
    for i in np.arange(POP_SIZE):
        generation_fitness[i] = fitness(population[i])

        if generation_fitness[i] > best_fitness:
            best_fitness = generation_fitness[i]
            best_individual = population[i]
            best_index = i


    half_cut = POP_SIZE//2
    generation_count = 0 # Controla a quantidade máxima de gerações
    no_change_count = 0 # Controla a quantidade de gerações sem mudança
    logs: list[str] = [] # controla as informações de output

    df = pd.DataFrame()
    df["Cromossomes"] = population
    df["Fitness"] = generation_fitness
    df["Normalized_Fitness"] = np.zeros(shape=[POP_SIZE])
    df["Normalized_Fitness_Cummulative_Sum"] = np.zeros(shape=[POP_SIZE])


    # Loop principal
    while True:

        # print(generation_count)
        if not (best_fitness < target_fitness):
            stop_by = "Reach fitness target"
            break
        if not (generation_count < MAX_GENERATIONS):
            stop_by = "Reach MAX_GENERATIONS"
            break
        if not (no_change_count < MAX_NO_CHANGE_GENERATIONS):
            stop_by = "Reach MAX_NO_CHANGE_GENERATIONS"
            break
        
        # Ordena os cromossomos por fitness
        df.sort_values(by='Fitness', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)


        # Calcula Normalized fitness e Cummulative fitness para usar na roleta
        df['Normalized_Fitness'] = df["Fitness"] / df["Fitness"].sum()
        df["Normalized_Fitness_Cummulative_Sum"] = df["Normalized_Fitness"].cumsum()
        

        # Seleção por roleta que seleciona 50% (half_cut) dos cromossomos
        selected_mask = np.full(POP_SIZE, False, dtype = bool)
        unique_indexes = set()
        while len(unique_indexes) < half_cut:
            random_num = np.random.rand(1)[0]
            temp = df["Normalized_Fitness_Cummulative_Sum"]
            temp = temp.append(pd.Series(random_num))
            temp.sort_values(ascending = True, inplace = True)
            temp.reset_index(drop = True, inplace = True)
            selected_index = np.where(temp.values == random_num)[0][0]

            selected_mask[selected_index] = True
            unique_indexes.add(selected_index)
        
        # Aplica crossover nos selecionados
        selected_indexes = np.where(selected_mask == True)[0]

        # Aplica mutação nos não selecionados pela roleta
        not_selected_indexes = np.where(selected_mask == False)[0]

        
        # selected_indexes = unique_indexes # Alternativa que auto ordena por fitness
        it = iter(selected_indexes)
        for i, j in zip(it, it):
            if np.random.rand(1) <= CROSSOVER_RATE:
                # Pega um par de cromossomos
                c1 = df["Cromossomes"][i]
                c2 = df["Cromossomes"][j]
                new_pair = crossover(c1, c2, N_POINT)

                # Atualiza geração
                df.at[i, 'Cromossomes'] = new_pair[0]
                df.at[j, 'Cromossomes'] = new_pair[1]

        
        for i in not_selected_indexes:
            if np.random.rand(1) <= MUTATION_RATE:
                cromossome = df["Cromossomes"][i]
                new_cromossome = mutation(cromossome, bag_of_artifacts, useless)

                # Atualiza geração
                df.at[i, 'Cromossomes'] = new_cromossome
        

        # Calcula o fitness da geração atual
        for i in np.arange(POP_SIZE):
            generation_fitness[i] = fitness(df["Cromossomes"][i])

            if generation_fitness[i] > best_fitness:
                best_fitness = generation_fitness[i]
                best_individual = df["Cromossomes"][i]
                best_index = i
                # print("reset chance count")
                no_change_count = 0 # Reseta o contador de mudanças

        df["Fitness"] = generation_fitness # Atualiza o fitness

        generation_count += 1
        no_change_count += 1

        # Log das informações da geração
        logs.append(f'best_fitness:{best_fitness}|best_individual:{best_individual}|sum:{df["Fitness"].sum()}|mean:{df["Fitness"].mean()}\n')

    return {
        'best_fitness': best_fitness,
        'best_individual': best_individual,
        'best_index': best_index,
        'stop_by': stop_by,
        'logs': logs
    }

print("ÍNÍCIO")
if __name__ == '__main__':
    INPUTS = ["Hu Tao + Báculo de Homa R1 + Habilidade Elemental + Ataque Carregado", "Zhongli + Borla Preta R5 + Dano de Absorção do Escudo"]
    USELESS_STATS = [["DEF", "DEF%", "ER", "Hydro", "Cryo", "Electro", "Geo", "Anemo", "Healing"], ["DEF", "DEF%", "Hydro", "Cryo", "Electro", "Pyro", "Anemo", "Healing"]]
    file_names = ["first", "second"]
    functions = [fitness_1, fitness_2]
    targets = [30000, 50000] # 30k dano e 50k absorção de escudo

    seeds = [seed for seed in range(0, 30, 1)]

    for function, target, file_name, useless_stats, input_ in \
        zip(functions, targets, file_names, USELESS_STATS, INPUTS):
            
        for seed in seeds:
            result = GA(function, target, useless_stats, seed)

            print("Resultados")
            print(f"Combinação: {input_}")
            print(f"Melhor output da build: { result['best_fitness'] }")
            print(f"Melhor build: { result['best_individual'] }")
            print(f"Index da build: { result['best_index'] }")
            print(f"Stop by: { result['stop_by'] }")
            # print(f"Log: { result['logs'] }")
            print("=------------=")

            # Escreve num arquivo os resultados
            with open(f"GA_{file_name}_{seed}.txt", "w") as f:
                for log in result['logs']:
                    f.writelines(log)
print("FIM")
