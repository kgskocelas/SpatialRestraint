from pyvarco import CombinationCollector
import argparse, os, errno
from util_funcs import * 

#### BEGIN CONFIGURATION ####
parser = argparse.ArgumentParser(description='Job generation for timing distributions', prefix_chars='@')
parser.add_argument('@@executable_path', type=str, help='Path to SpatialRestraint executable')
parser.add_argument('@@output_dir',      type=str, help='Root directory where timing data will ' + \
        'be saved')
parser.add_argument('@@job_dir',         type=str, help='Directory where job timing data will ' + \
        'be saved')
parser.add_argument('@@distribution_dir',type=str, help='Directory containing timing data ',  \
        default='')
parser.add_argument('@@ones',            type=str, help='Number of ones in ancestral genome. ' + \
        'Values separated by commas. X->Y,Z means every value between X and Y ', default = '50')
parser.add_argument('@@gens',            type=int, help='Number of generations to evolve',  \
        default = '5000')
parser.add_argument('@@cost',            type=str, help='Cost for each unrestrained cell. ' + \
        'Comma separated.', default = '0')
parser.add_argument('@@mc_size',         type=str, help='Multicell sizes to run. Size is one ' + \
        'side of ' + \
        'a square (e.g., 8 = 8x8 multicells. Comma separated.', default = '8,16,32,64,128,256,512')
parser.add_argument('@@pop_size',        type=str, help='Number of multicells in population.  ' + \
        'Comma separated.', default = '200')
parser.add_argument('@@mut_rate',        type=str, help='Mutation rate for multicells. Comma ' + \
        'separated.', default = '0.2')
parser.add_argument('@@cell_mut_rate',   type=str, help='Mutation rate for cells. Comma ' + \
        'separated.', default = '0.2')
parser.add_argument('@@samples',         type=int, help='Number of multicells to run.', \
        default = 1000)
parser.add_argument('@@threshold',        type=str,help='Number of ones requierd for restraint.' + \
        ' Comma separated ints.', default = '50')
parser.add_argument('@@reps',            type=int, help='Number of evolutionary replicates per ' \
        + ' treatments', default = 100)
parser.add_argument('@@seed_offset',     type=int, help='First job starts with this seed and ' + \
        'then counts up from there', default = 0)
parser.add_argument('@@time',            type=str, help='Time per jobs. Format: HH:MM:SS', \
        default = '2:00:00')
parser.add_argument('@@memory',          type=str, help='Memory (typically gigs) per job. ' + \
        'Format: xG for x gigs', default = '1G')
# mgilson at https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
parser.add_argument('@@one_check',   dest='one_check', action='store_true', help='Pass -o')
parser.add_argument('@@multi_check', dest='one_check', action='store_false', help='Do not pass -o')
parser.set_defaults(one_check=True)
parser.add_argument('@@infinite',    dest='infinite', action='store_true', help='Pass -I')
parser.add_argument('@@finite',      dest='infinite', action='store_false', help='Do not pass -I')
parser.set_defaults(infinite=False)
parser.add_argument('@@enforce',     dest='enforce', action='store_true', help='Pass -e')
parser.add_argument('@@no-enforce',  dest='enforce', action='store_false', help='Do not pass -e')
parser.set_defaults(enforce=False)


args = parser.parse_args()
if(args.executable_path == None): 
    print('Error! Executable path not specified')
    exit(1)
if(args.output_dir == None):
    print('Error! Output directory not specified')
    exit(1)
if(args.job_dir == None):
    print('Error! Job directory not specified')
    exit(1)

#### BEGIN CONFIGURATION ####

# Where is the SpatialRestraint located?
executable_path = args.executable_path
# Where should we save *actual* output data (from the SpatialRestraint app)
output_dir = ensure_trailing_slash(args.output_dir)
# Where should we save the slurm scripts generated by this script?
job_dir = '../jobs/'
job_dir = ensure_trailing_slash(args.job_dir)

# If we are loading data, where should that data come from?
    # Note: this expects the directory to contain subdirectories, one for each MC size
    # e.g. ./foo/ where ./foo/ contains directories 512/ 256/ etc. 
    # Each numbered directory should contain the .dat files that will be loaded
distribution_data_dir = ensure_trailing_slash(args.distribution_dir)
# If true, the program will load in the samples from the multicell replicate time distributions
    # From disk
use_distribution_data = distribution_data_dir.strip() != '' 


# SpatialRestraint config options
    # Variables that are lists are used such that *every* combination is generated
combos = CombinationCollector()
combos.register_var('MCSIZE')
combos.register_var('COST')
combos.register_var('GENS')
combos.register_var('MUT')
combos.register_var('POP')
combos.register_var('SAMPLES')
combos.register_var('REPS')
combos.register_var('ONES')
combos.register_var('THRESH')
combos.register_var('CELLMUT')


combos.add_val('MCSIZE',    str_to_int_list(args.mc_size))
combos.add_val('COST',      str_to_int_list(args.cost))
combos.add_val('GENS',      [args.gens])
combos.add_val('MUT',       str_to_float_list(args.mut_rate))
combos.add_val('POP',       str_to_int_list(args.pop_size))
combos.add_val('SAMPLES',   [args.samples])
combos.add_val('REPS',      [args.reps])
combos.add_val('ONES',      str_to_int_list(args.ones))
combos.add_val('THRESH',    str_to_int_list(args.threshold))
combos.add_val('CELLMUT',  str_to_float_list(args.cell_mut_rate))

# Any extra flags to send to SpatialRestraint
extra_flags = '-v' 
if args.one_check:
    extra_flags += ' -o'
if args.infinite:
    extra_flags += ' -I'
if args.enforce:
    extra_flags += ' -e'

# This is a simple offset for the job id. If first batch is 0-1000, set this as 1000 to get 1000-2000
job_id_start = args.seed_offset

#### END CONFIGURATION ####

combo_list = combos.get_combos()

# Calculate the number of jobs we expect. 
    # We also print the actual number of jobs at the end. They should alwaya match. 
total_jobs = len(combo_list)
print('Expecting ' + str(total_jobs) + ' jobs...')
final_job_id = job_id_start + total_jobs
num_digits = len(str(final_job_id))


num_jobs = 0
cur_job_id = job_id_start
# Iterate through each combination of configuration variables
for condition_dict in combo_list:        
        num_jobs += 1
        cur_job_id += 1
        # Embed configuration options into filename
        job_id_str = str(cur_job_id)
        job_id_str = '0' * (num_digits - len(job_id_str)) + job_id_str
        filename_prefix = job_id_str + '_spatial_restraint__' + combos.get_str(condition_dict)
        # Write slurm job file using current configuration options
        with open(job_dir + filename_prefix + '.sb', 'w') as fp_job:
            fp_job.write('#!/bin/bash --login' + '\n')
            fp_job.write('' + '\n')
            # Change the time per job here!
            fp_job.write('#SBATCH --time=' + args.time + '\n')
            fp_job.write('#SBATCH --nodes=1' + '\n')
            fp_job.write('#SBATCH --ntasks=1' + '\n')
            fp_job.write('#SBATCH --cpus-per-task=1' + '\n')
            fp_job.write('#SBATCH --mem-per-cpu=' + args.memory + '\n')
            fp_job.write('#SBATCH --job-name sr_evo_' + job_id_str + '\n')
            fp_job.write('#SBATCH --array=1-1' + '\n')
            fp_job.write('#SBATCH --output='  + \
                output_dir + filename_prefix + '_%a__slurm.out' + \
                '\n')
            fp_job.write('' + '\n')
            fp_job.write('module purge' + '\n')
            fp_job.write('module load GCC/9.1.0-2.32' + '\n')
            fp_job.write('' + '\n')
            fp_job.write('mkdir -p ' + output_dir + filename_prefix + '\n') 
            fp_job.write('' + '\n')
            fp_job.write('RANDOM_SEED=' + str(cur_job_id)+ '\n')

            command_str = executable_path
            command_str += ' -a ' + str(condition_dict['ONES'])
            command_str += ' -c ' + str(condition_dict['MCSIZE'])
            command_str += ' -g ' + str(condition_dict['GENS'])
            command_str += ' -m ' + str(condition_dict['MUT'])
            command_str += ' -r ' + str(condition_dict['THRESH'])
            command_str += ' -E ' + output_dir + filename_prefix + \
                '/${SLURM_ARRAY_TASK_ID}_evolution.dat'
            command_str += ' -C ' + output_dir + filename_prefix + \
                '/${SLURM_ARRAY_TASK_ID}_config.dat'
            command_str += ' -s ' + str(condition_dict['SAMPLES'])
            command_str += ' -d ' + str(condition_dict['REPS'])
            command_str += ' -u ' + str(condition_dict['COST'])
            command_str += ' -p ' + str(condition_dict['POP'])
            command_str += ' -w ${RANDOM_SEED}' 
            if(use_distribution_data):
                command_str += ' -L ' + \
                    distribution_data_dir + \
                    'thresh__' + str(condition_dict['THRESH']) + '/' + \
                    'cell_mut__' + str(condition_dict['CELLMUT']) + '/' + \
                    'mcsize__' + str(condition_dict['MCSIZE']) + '/'
            
            command_str += ' ' + extra_flags + ' '
            
            fp_job.write('echo "' + command_str + '"\n')
            fp_job.write('time ' + command_str + '\n')
            fp_job.write('\n')
            fp_job.write('scontrol show job $SLURM_JOB_ID' + '\n')

print('Generated ' +  str(num_jobs) + '!')
