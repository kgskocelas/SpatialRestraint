from pyvarco import CombinationCollector

#### BEGIN CONFIGURATION ####

# Where is the SpatialRestraint located?
executable_path = '/mnt/home/fergu358/research/rogue_cell/SpatialRestraint/SpatialRestraint'
# Where should we save *actual* output data (from the SpatialRestraint app)
scratch_dir = '/mnt/gs18/scratch/users/fergu358/rogue_cell/SpatialRestraint/'
# Where should we save the slurm scripts generated by this script?
job_dir = './jobs/'

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

combos.add_val('MCSIZE',  [1024,512,256,128,64,32,16,8])
combos.add_val('COST',    [0,100])
combos.add_val('GENS',    [10000])
combos.add_val('MUT',     [0.2])
combos.add_val('POP',     [10000])
combos.add_val('SAMPLES', [1000])
combos.add_val('REPS',    [100])

# Any extra flags to send to SpatialRestraint
extra_flags = '-o -v'

# This is a simple offset for the job id. If first batch is 0-1000, set this as 1000 to get 1000-2000
job_id_start = 1000

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
            fp_job.write('#SBATCH --time=167:00:00' + '\n')
            fp_job.write('#SBATCH --nodes=1' + '\n')
            fp_job.write('#SBATCH --ntasks=1' + '\n')
            fp_job.write('#SBATCH --cpus-per-task=1' + '\n')
            fp_job.write('#SBATCH --mem-per-cpu=1G' + '\n')
            fp_job.write('#SBATCH --job-name Spatial_Restraint' + '\n')
            fp_job.write('#SBATCH --array=1-1' + '\n')
            fp_job.write('#SBATCH --output='  + \
                scratch_dir + filename_prefix + '_%a__slurm.out' + \
                '\n')
            fp_job.write('' + '\n')
            fp_job.write('module purge' + '\n')
            fp_job.write('module load GCC/9.1.0-2.32' + '\n')
            fp_job.write('' + '\n')
            fp_job.write('mkdir -p ' + scratch_dir + filename_prefix + '\n') 
            fp_job.write('' + '\n')

            command_str = executable_path
            command_str += ' -c ' + str(condition_dict['MCSIZE'])
            command_str += ' -g ' + str(condition_dict['GENS'])
            command_str += ' -m ' + str(condition_dict['MUT'])
            command_str += ' -E ' + scratch_dir + filename_prefix + \
                '/${SLURM_ARRAY_TASK_ID}_evolution.dat'
            command_str += ' -s ' + str(condition_dict['SAMPLES'])
            command_str += ' -d ' + str(condition_dict['REPS'])
            command_str += ' -u ' + str(condition_dict['COST'])
            command_str += ' -p ' + str(condition_dict['POP'])
            command_str += ' ' + extra_flags + ' '
            
            fp_job.write('echo "' + command_str + '"\n')
            fp_job.write('time ' + command_str + '\n')
            fp_job.write('\n')
            fp_job.write('scontrol show job $SLURM_JOB_ID' + '\n')

print('Generated ' +  str(num_jobs) + '!')
