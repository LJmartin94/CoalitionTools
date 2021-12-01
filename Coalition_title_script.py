# # Max requests is 20 per minute
import os
import yaml

from Helsinki_42API_interface import ic

# Specify Codam as campus_id
campus_id = 14
staff_privileges = 0
print_summary = 1
vela_coalition_id = 60
# Vela title IDs = 424-459
cetus_coalition_id = 59
pyxis_coalition_id = 58


def main():
    print("Script started")
    give_coalition_titles(vela_coalition_id)


def give_coalition_titles(coalition_id):
    # First we make a snapshot of the current state of the coalition and its members with one API call
    # (this reduces the overall number of API calls & prevents ranks changing whilst titles are still being calculated)
    snapshot_bundle = make_coalition_state_snapshot(coalition_id)

    # Then we make a 2D array,
    # per student it has fields for a student's id, rank, 'abstract_title', intra title_id, and username.
    # The actual title_id and username are added later, these initially just have placeholders.
    student_rank_info = make_student_rank_info(snapshot_bundle)
    coalition_titles = make_title_id_array(coalition_id)
    student_rank_info = append_equipped_titles(student_rank_info, coalition_titles)

    # To print an optional summary of who has what title, set print_summary to 1 in the above global variables.
    # This does slow down the program however,
    # as it makes a separate API call to fetch the login names of all un-anonymised Codam students.
    if print_summary == 1:
        student_rank_info = append_login_names(student_rank_info)
        for entry in student_rank_info:
            print(entry)


def make_title_id_array(coalition_id):
    title_id_array = [0 for _ in range(36)]
    coalition_spec = 'vela'
    if coalition_id == cetus_coalition_id:
        coalition_spec = 'cetus'
    if coalition_id == pyxis_coalition_id:
        coalition_spec = 'pyxis'
    base_dir = os.path.dirname(os.path.realpath(__file__))
    with open(base_dir + '/title_config.yml', 'r') as cfg_stream:
        config = yaml.load(cfg_stream, Loader=yaml.BaseLoader)
        x = 0
        for _ in range(36):
            title_id_array[x] = config['all_titles'][coalition_spec][str(x + 1)]
            x += 1
    return title_id_array



def make_coalition_state_snapshot(coalition_id) -> object:
    snapshot = get_all_users_in_coalition(coalition_id)
    number_of_students = 0
    lowest_rank = 1
    for entry in snapshot:
        number_of_students += 1
        if entry['rank'] > lowest_rank:
            lowest_rank = entry['rank']
    snapshot_bundle = [snapshot, number_of_students, lowest_rank]
    return snapshot_bundle


def get_all_users_in_coalition(coalition_id) -> object:
    payload = {
        "sort": "user_id"
    }
    data = ic.pages_threaded("coalitions/" + str(coalition_id) + "/coalitions_users", params=payload)
    return data


def make_student_rank_info(snapshot_bundle):
    coalition_snapshot = snapshot_bundle[0]
    number_of_students = snapshot_bundle[1]
    lowest_rank = snapshot_bundle[2]
    student_rank_info = [[] for _ in range(number_of_students)]
    x = 0
    for entry in coalition_snapshot:
        student_rank_info[x] = [entry['user_id'], entry['rank'], "titles: ", "username", entry['score'], "location"]
        x += 1
    # Sort the list by rank because why not
    student_rank_info = sort_by_rank(student_rank_info)
    return student_rank_info


def sort_by_rank(student_rank_info):
    return sorted(student_rank_info, key=lambda x: x[1])


def append_login_names(student_rank_info):
    print("Fetching all students from specified campus:")
    ic.progress_bar = True
    payload = {
        "range[login]": "4,zzz",
        "sort": "login"
    }
    all_students = ic.pages_threaded("campus/" + str(campus_id) + "/users", params=payload)
    for entry in student_rank_info:
        for kvp in all_students:
            if kvp['id'] == entry[0]:
                entry[3] = kvp['login']
                entry[5] = kvp['location']
                # titles = get_student_title(kvp['id'])
                # for title in titles:
                #     entry[2] = entry[2] + " " + title['name'] + ","
    return student_rank_info


def append_equipped_titles(student_rank_info, titles):
    equipped_titles = 0
    for title_id in titles:
        title_owners = get_ids_of_students_with_title(title_id)
        for user in title_owners:
            if user['selected'] == True:
                for student in student_rank_info:
                    if student[0] == user['user_id']:
                        student[2] = student[2] + str(user['title_id'])
                        equipped_titles += 1
    print("Coalition titles equipped: " + str(equipped_titles))
    return student_rank_info

def get_ids_of_students_with_title(title_id):
    ic.progress_bar = False
    payload = {
    }
    data = ic.pages_threaded("titles/" + str(title_id) + "/titles_users", params=payload)
    return data


def get_student_title(student_id):
    ic.progress_bar = False
    payload = {
    }
    data = ic.pages_threaded("users/" + str(student_id) + "/titles", params=payload)
    return data

if __name__ == "__main__":
    main()
