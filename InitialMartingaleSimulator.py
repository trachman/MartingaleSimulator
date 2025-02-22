import random
import matplotlib.pyplot as plt
import numpy as np


'''
This essentially proved that Martingale is alright for the true martingale case.
50/50 odds and doubling down until you make double your initial money is somewhat profitable
if you have infinite funds.

In a thousand simulations, we won 99.9% of the time.
We lost a total of our CASH_AVAILABLE once. This was set to $50,000.
We were net positive $49,900.

Now, we tweaked this simulation for typical blackjack parameters.
Win Percentage of 42.22%
We also put a max bet size of 500.
We were net negative by a large margin. See the BlackJackMartingaleResults folder.

So this got me thinking. Martingale sucks, but how good is real card counting?

I will implement a blackjack simulator to find out.
'''

# The goal of martingale is to double your money.
# The rules are as follows:
# 1. Bet 1 unit
# 2. If you win, great!
# 3. If you didn't win, double your bet and repeat until you hit your goal of doubling your initial unit.
#
CASH_AVAILABLE  = 50_000
UNIT            = 100
MAX_BET         = CASH_AVAILABLE # Realistically at a casino this is much lower, like 500 a bet or something
GOAL            = UNIT
WIN_PROBABILITY = 0.5 # Blackjack has a realistic probability of 0.4222
NUM_SIMULATIONS = 1000

print(f'You are bringing ${CASH_AVAILABLE} to the casino.')
print(f'Your base bet is ${UNIT}')
print(f'Your goal winnings are ${GOAL}')

# CASH_AVAILABLE  = int(input('How much money are you bringing to the casino? $'))
# UNIT            = int(input('What is your base bet? $'))
# GOAL            = int(input('What do you want to walk home with? $'))

def flip_coin() -> bool:
    '''
    Returns True if heads, returns false, otherwise. 
    Based off of your win probability.
    '''
    return random.uniform(0, 1) < WIN_PROBABILITY

def average_amount_staked(stakes) -> float:
    '''
    Given a list of amounts staked for a number of simulations. Return the average.
    '''
    average_amount_staked = 0
    for stake in stakes: average_amount_staked += stake
    average_amount_staked = average_amount_staked / len(stakes)
    return round(average_amount_staked, 2)

def average_number_of_bets(counts) -> int:
    '''
    Given a list of number of stakes for a number of simulations. Return the average.
    '''
    average_number_of_bets = 0
    for count in counts: average_number_of_bets += count
    average_number_of_bets = average_number_of_bets / len(counts)
    return int(average_number_of_bets)

def num_wins(results) -> int:
    '''
    Given a list of boolean results. Return the number that are true.
    '''
    num_wins = 0
    for result in results:
        if result:
            num_wins += 1
    return num_wins

def win_percentage(results) -> float:
    '''
    Given a list of boolean results. Return the percentage that are true.
    '''
    return round((num_wins(results) / len(results)) * 100, 2)

# Run a thousand simulations
print(f'\nRunning {NUM_SIMULATIONS} simulations ... \n')

stakes  = []
counts  = []
results = []
max_amount_in_the_hole = 0
max_bet                = 0

for _ in range(NUM_SIMULATIONS):
    cash                   = []
    current_cash_available = CASH_AVAILABLE
    current_bet            = UNIT
    current_money          = 0
    count                  = 0
    total_amount_staked    = 0

    while current_money < GOAL and current_cash_available > 0:
        cash.append(current_cash_available)
        count                  += 1
        total_amount_staked    += current_bet
        max_amount_in_the_hole  = max(max_amount_in_the_hole, CASH_AVAILABLE - current_cash_available)
        max_bet                 = max(max_bet, current_bet)

        if flip_coin():
            current_cash_available += current_bet
            current_money          += current_bet
            current_bet             = UNIT
        else:
            current_cash_available -= current_bet
            current_money          -= current_bet
            current_bet            *= 2
            if current_bet > MAX_BET: current_bet = MAX_BET

    count += 1
    cash.append(current_cash_available)
    results.append(current_money >= GOAL)
    stakes.append(total_amount_staked)
    counts.append(count)

    # Find average value of cash for plotting notes:
    min_cash = 999999999999
    max_cash = 0
    for c in cash:
        min_cash = min(min_cash, c)
        max_cash = max(max_cash, c)

    # Save the plots of each simulation to the Plots folder
    x_axis_baseline = np.array([1, count + 1])
    y_axis_baseline = np.array([CASH_AVAILABLE, CASH_AVAILABLE])
    plt.plot(x_axis_baseline, y_axis_baseline, color='red')
    x_axis = np.array([i for i in range(1, count + 1)])
    y_axis = np.array(cash)
    plt.plot(x_axis, y_axis, color='blue')
    plt.xlabel('Bet #')
    plt.ylabel('Cash Available')
    plt.title(f'Martingale Simulation #{_ + 1}')
    plt.text(1, ((max_cash - min_cash) * 0.8) + min_cash, f'Cash Available: ${CASH_AVAILABLE}\nGoal Winnings: ${GOAL}\nInitial Bet:         ${UNIT}', fontsize=8)
    plt.savefig(f'Plots\\Simulation{_ + 1}')
    plt.cla()
    plt.clf()

# Given the win percentage, did you break even?
number_of_wins   = num_wins(results)
number_of_losses = NUM_SIMULATIONS - number_of_wins
amount_won       = number_of_wins * GOAL
amount_lost      = number_of_losses * CASH_AVAILABLE

# Output the notable results of all your simulations
print(f'The percentage of the time you won: %{win_percentage(results)}')
print(f'The average number of bets: {average_number_of_bets(counts)}')
print(f'The average amount staked is: ${average_amount_staked(stakes)}')
print(f'The maximum amount you were in the hole: ${max_amount_in_the_hole}')
print(f'Your max bet was: ${max_bet}')
print(f'The total amount you won: ${amount_won}')
print(f'The total amount you lost: ${amount_lost}')
print(f'The total profit: ${amount_won - amount_lost}')