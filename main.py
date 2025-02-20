import math
import random
import sys
from typing import Optional

# https://www.statista.com/statistics/190356/wheat-yield-per-harvested-acre-in-the-us-from-2000/
BSH_PER_ACRE = 40
BSH_SEED_PER_ACRE = 2
# http://www.waldeneffect.org/blog/Calories_per_acre_for_various_foods/
CALORIE_PER_ACRE = 6_400_000
CALORIE_PER_PERSON_PER_DAY = 1500
PERSON_DAY_PER_ACRE = round(CALORIE_PER_ACRE / CALORIE_PER_PERSON_PER_DAY)
PERSON_DAY_PER_BSH = round(PERSON_DAY_PER_ACRE / BSH_PER_ACRE)
PERON_PER_ACRE = 2


class Market:

    def __init__(self, price, units):
        self.price = price
        self.units = units
        self.offers = []
        self.world = None # type: Optional[World] initialized by World.add_market

    def adjust_price(self, price):
        if price > self.price:
            percent_greater = 1 + (price - self.price) / self.price
            percent_greater *= 1.1
            self.price *= percent_greater
        else:
            percent_less = 1 - (self.price - price) / self.price
            percent_less *= 0.9
            self.price *= percent_less
        self.price = random.uniform(self.price * 0.9, self.price * 1.1)

    def settle_offers(self):
        if len(self.offers) == 0 and self.price > 3:
            self.adjust_price(self.price * 0.8)
            return
        while self.offers:
            offer = self.offers.pop(0)
            name, action, units, price = offer
            if action == "buy":
                if price >= self.price:
                    available_units = min(units, self.units)
                    self.world.city_states[name].bushels -= price * available_units
                    self.world.city_states[name].acres += available_units
                    self.units -= available_units
                    self.adjust_price(price)
                else:
                    print(f"Buy price {price} is less than market price {self.price}.")
            elif action == "sell":
                if price <= self.price:
                    self.world.city_states[name].bushels -= price * units
                    self.world.city_states[name].acres += units
                    self.units += units
                    self.adjust_price(price)
                else:
                    print(f"Sale price {price} is greater than market price {self.price}.")

    def make_offer(self, uid, action, units, price):
        self.offers.append((uid, action, units, price))


class CityState:

    def __init__(self, name: str, population: int, acres: int, bushels: int):
        self.name = name
        self.year = 1
        self.population = population
        self.army = 0
        self.world = None # type: Optional[World] initialized by World.add_city_state
        self.bushels = bushels
        self.acres = acres
        self.planted_acres = 0
        self.starved = 0
        self.born = self.population

    def print_status(self, compact=False):
        if compact:
            print(f"\n>>> {self.name}: {self.year} | Pop: {self.population} | Mil.: {self.army} | Bsh: {self.bushels:.1f} | Acre: {self.acres} | ☠️: {self.starved}")
        else:
            print("\n" + "-" * 20)
            print(f"  State: {self.name}")
            print(f"  Year: {self.year}")
            print(f"  Pop.: {self.population}")
            print(f"  Mil.: {self.army}")
            print(f"  Bshl: {self.bushels}")
            print(f"  Acre: {self.acres}")
            print(f"  ☠️☠️☠️☠️: {self.starved}")
            print("-" * 20)

    def land_price(self):
        return random.randint(15, 25)
    
    def land_transaction(self, acres: int, price: float):
        '''Buy or sell land. Negative acres means sell. Positive acres means buy.
        '''
        if acres == 0:
            return
        if acres < 0: # sell
            self.world.market.make_offer(self.name, "sell", acres, price)
        if acres > 0: # buy
            self.world.market.make_offer(self.name, "buy", acres, price)

    def offer_land_transaction(self):
        price = self.world.market.price
        max_acres = self.bushels / price
        min_acres = -self.acres
        print(f"\nLand price: {price:.2f}")
        print(f"Max acres: {max_acres:.2f} for {max_acres * price:.2f} bushels")
        print(f"Min acres: {min_acres:.2f} for {-min_acres * price:.2f} bushels")
        acres = int(input("How many acres? "))
        if acres < min_acres or acres > max_acres:
            print(f"Invalid number of acres. Must be between {min_acres} and {max_acres}.")
            raise ValueError("Invalid number of acres in land transaction.")
        if acres != 0:
            price = float(input("Price per acre? "))
            self.land_transaction(acres, price)
    
    def workable_acres(self):
        '''Return the number of acres that can be worked by the population.
        '''
        return min(self.acres, self.population // PERON_PER_ACRE)
    
    def offer_plant_bushels(self):
        workable_acres = self.workable_acres()
        self.print_status(compact=True)
        print(f"Number of bushels to plant {workable_acres} acres: {workable_acres * BSH_SEED_PER_ACRE} bushels")
        bushels = int(input("How many bushels? "))
        self.plant(bushels)

    def plant(self, bushels: int):
        self.planted_acres = bushels // BSH_SEED_PER_ACRE
        self.bushels -= bushels
    
    def harvest(self):
        acres = min(self.planted_acres, self.workable_acres())
        self.bushels += acres * BSH_PER_ACRE
        self.planted_acres = 0

    def distribute_number_bushels(self, bushels: float):
        '''Update population to match the number of bushels fed.
        '''
        if bushels > self.bushels:
            bushels = self.bushels
        self.bushels -= bushels
        people = int(math.ceil(bushels / 3))
        starved = self.population - people
        if starved > 0:
            self.population = people
            self.starved += starved
            return starved
        else:
            return 0

    def offer_distribute_food(self):
        self.print_status(compact=True)
        food_required = self.population * 3 + self.army * 5
        print(f"Number of bushels to feed population: {food_required} bushels")
        bushels = float(input("How many bushels? "))
        starved = self.distribute_number_bushels(bushels)
        return starved

    def birth_rate(self):
        return random.uniform(0.1, 3)
    
    def death_rate(self):
        return random.uniform(0.0, 0.2)
    
    def migration(self):
        change_percent = 0.2
        pop = self.population
        new_pop_delta = int(random.uniform(-pop * change_percent, pop * change_percent))
        if new_pop_delta < -1:
            print(f"{-new_pop_delta} people left.")
        elif new_pop_delta == -1:
            print(f"{-new_pop_delta} person left.")
        elif new_pop_delta == 0:
            print("No one arrived or left.")
        elif new_pop_delta == 1:
            print(f"{new_pop_delta} person arrived.")
        elif new_pop_delta > 1:
            print(f"{new_pop_delta} people arrived.")
        self.population += new_pop_delta
    
    def manage_population(self, starved: int):
        print(f"\n{starved} people starved.")
        deaths = int(self.population * self.death_rate())
        if deaths == 1:
            print(f"{deaths} person died of natural causes.")
        else:
            print(f"{deaths} people died of natural causes.")
        self.population -= deaths
        births = int(self.population * self.birth_rate())
        self.born += births
        if births == 1:
            print(f"{births} person was born.")
        else:
            print(f"{births} people were born.")
        self.population += births
        self.migration()

    def offer_raise_army(self):
        self.print_status(compact=True)
        print(f"Size of army: {self.army}")
        solidiers = int(input("How many solidiers to recruit? "))
        self.army += solidiers
        self.bushels -= solidiers * 5

    def offer_attack(self):
        print(f"Size of army: {self.army}")
        defender = input("Who do you want to attack? ")
        if defender:
            if defender in self.world.city_states:
                self.world.attack(self.name, defender)
            else:
                print("Defender not registered.")
        
    def maybe_rats(self):
        if random.random() < 0.85:
            return
        print("\n☠️ Rats! ☠️")
        lost = int(self.bushels * random.choice([0.25, 0.5, 1.0]))
        print(f"{lost} bushels lost to rats.")
        self.bushels -= lost

    def maybe_plague(self):
        if random.random() < 0.85:
            return
        print("\n☠️ Plague! ☠️")
        lost = int(self.population * random.uniform(0.4, 0.6))
        print(f"{lost} people lost to plague.")
        self.population -= lost

    def disaster(self):
        self.maybe_rats()
        self.maybe_plague()

    def step(self):
        self.print_status()
        self.offer_land_transaction()
        self.world.market.settle_offers()
        self.offer_plant_bushels()
        starved = self.offer_distribute_food()
        self.manage_population(starved)
        self.harvest()
        self.disaster()
        self.offer_raise_army()
        if self.army > 0:
            self.offer_attack()
        self.year += 1

class World:

    def __init__(self):
        self.market = None
        self.city_states = {}

    def add_market(self, market: Market):
        market.world = self
        self.market = market

    def add_city_state(self, city_state: CityState):
        if city_state.name not in self.city_states:
            city_state.world = self
            self.city_states[city_state.name] = city_state

    def attack(self, attacker, defender):
        '''This method breaks up the attack into three parts:

        1. Compute the attack - logic that computes deltas
        2. Resolve the attack - side effects to update combatants
        3. Report the attack - side effects to update the user
        '''
        attack = self.compute_attack(attacker, defender)
        self.resolve_attack(attack)
        self.report_attack(attack)

    def compute_attack(self, attacker, defender):
        if attacker not in self.city_states:
            raise ValueError("Attacker not registered.")
        if defender not in self.city_states:
            raise ValueError("Defender not registered.")
        result = {
            'attacker': attacker,
            'defender': defender,
            'attacker_bushels_delta': 0,
            'defender_bushels_delta': 0,
            'attacker_acres_delta': 0,
            'defender_acres_delta': 0,
            'attacker_army_delta': 0,
            'defender_army_delta': 0,
            'victor': None,
            'loser': None,
        }
        attacker = self.city_states[attacker]
        defender = self.city_states[defender]
        if attacker.army > defender.army * 1.75:
            result['attacker_bushels_delta'] = defender.bushels * 0.75
            result['defender_bushels_delta'] = -defender.bushels * 0.75
            result['attacker_acres_delta'] = defender.acres * 0.25
            result['defender_acres_delta'] = -defender.acres * 0.25
            result['attacker_army_delta'] = -random.randint(0, attacker.army)
            result['defender_army_delta'] = -defender.army
            result['victor'] = attacker.name
            result['loser'] = defender.name
        else:
            result['attacker_bushels_delta'] = -attacker.bushels * 0.25
            result['defender_bushels_delta'] = attacker.bushels * 0.25
            result['attacker_army_delta'] = -random.randint(0, int(defender.army * 0.25))
            result['victor'] = defender.name
            result['loser'] = attacker.name
        return result
    
    def resolve_attack(self, attack):
        attacker = self.city_states[attack['attacker']]
        defender = self.city_states[attack['defender']]
        attacker.bushels += attack['attacker_bushels_delta']
        defender.bushels += attack['defender_bushels_delta']
        attacker.acres += attack['attacker_acres_delta']
        defender.acres += attack['defender_acres_delta']
        attacker.army += attack['attacker_army_delta']
        defender.army += attack['defender_army_delta']

    def report_attack(self, attack):
        print(f"\n{attack.get('victor')} won the battle against {attack.get('loser')}.")
        self.city_states[attack.get('victor')].print_status(compact=True)
        self.city_states[attack.get('loser')].print_status(compact=True)

def print_score(state):
    print("-" * 20)
    print(f"State: {state.name}")
    print(f"Years: {state.year-1}")
    print(f"Starved: {state.starved}")
    print(f"Born: {state.born}")
    print(f"Score: {100 * (1 - state.starved/state.born):.2f}%")

def main(years=10):
    market = Market(
        price=random.randint(10, 20),
        units=random.randint(100, 300),
    )
    world = World()
    world.add_market(market)
    names = ["Sumer", "Asher"]
    for name in names:
        state = CityState(
            name,
            population=random.randint(10, 30),
            acres=random.randint(10, 30),
            bushels=random.randint(50, 100),
        )
        world.add_city_state(state)
    for _ in range(years):
        for state in world.city_states.values():
            state.step()
    print()
    for state in world.city_states.values():
        print_score(state)
    print("-" * 20)

if __name__ == "__main__":
    years = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    main(years)
