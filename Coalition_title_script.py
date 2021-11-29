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

    # To print an optional summary of who has what title, set print_summary to 1 in the above global variables.
    # This does slow down the program however,
    # as it makes a separate API call to fetch the login names of all un-anonymised Codam students.
    if print_summary == 1:
        student_rank_info = append_login_names(student_rank_info)
        for entry in student_rank_info:
            print(entry)


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
        student_rank_info[x] = [entry['user_id'], entry['rank'], "title_id", "username", entry['score'], "location"]
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
    return student_rank_info


if __name__ == "__main__":
    main()
