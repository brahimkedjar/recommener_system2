
    
import psycopg2
from geopy.distance import distance
from flask import Flask, request, jsonify
import json
from math import radians
import psycopg2
from statistics import mean
from geopy.distance import distance
app = Flask(__name__)
def get_recommendations(doctor_id, max_distance, max_members):
    # Connect to the database
    conn = psycopg2.connect(database="sihati", user="sihati",
                            password="Daddy22mars_", host="41.111.206.183", port="5432")
    c = conn.cursor()
    # Retrieve the doctor's specialty and baladia
    c.execute('SELECT specialite, selected_wilaya, latitude, longitude FROM doctors WHERE id=%s', (doctor_id,))
    specialite, selected_wilaya, doctor_lat, doctor_lng = c.fetchone()

    # Query the groups table to retrieve group_id and baladia
    c.execute('SELECT group_id, baladia, latitude, longitude FROM groups WHERE speciality=%s', (specialite,))
    groups = c.fetchall()

    # Filter the groups based on the baladia being included in the selected_wilaya values of the doctor
    filtered_groups = [(group_id, baladia, group_lat, group_lng) for group_id, baladia, group_lat, group_lng in groups if any(wilaya.strip() == baladia for wilaya in selected_wilaya)]


    # Calculate the distance between the doctor's location and the centroid of each filtered group
    group_distances = {}
    for group in filtered_groups:
        group_id, baladia, group_lat, group_lng = group
        group_center = (group_lat, group_lng)
        dist = distance((doctor_lat, doctor_lng), group_center).km
        if group_id in group_distances:
            group_distances[group_id].append(dist)
        else:
            group_distances[group_id] = [dist]

    # Calculate the mean distance of each group
    group_means = {}
    for group_id, dists in group_distances.items():
        mean_dist = sum(dists) / len(dists)
        group_means[group_id] = mean_dist

    # Filter the groups based on the maximum distance
    filtered_groups = [group for group in group_means.items() if group[1] <= max_distance]

    # Filter the groups based on the number of patients
    filtered_groups = [(group_id, baladia) for group_id, mean_distance in filtered_groups if get_number_of_patients(group_id) <= max_members and get_number_of_patients(group_id) >= max_members - 5]

    # Create a dictionary to store patients grouped by group_id
    group_patients = {}
    for group_id, baladia in filtered_groups:
        c.execute('SELECT name, latitude, longitude FROM patients WHERE %s = ANY(group_id)', (group_id,))
        patients = c.fetchall()
        for patient in patients:
            name, latitude, longitude = patient
            if group_id in group_patients:
                group_patients[group_id].append((name, latitude, longitude))
            else:
                group_patients[group_id] = [(name, latitude, longitude)]

    # Create the final list of recommendations
    recommendations = []
    for group_id, baladia in filtered_groups:
        patients = group_patients[group_id]
        recommendations.append((group_id, baladia, patients))

    print(recommendations)
    return recommendations


def get_number_of_patients(group_id):
    # Connect to the database
    conn = psycopg2.connect(database="db", user="postgres",
                            password="crb12345", host="localhost", port="5432")
    c = conn.cursor()
    # Retrieve the number of patients in the group from groups_numbers table
    c.execute('SELECT patients_number FROM groups_numbers WHERE group_id=%s', (group_id,))
    count = c.fetchone()[0]
    return count


@app.route('/recommender_patients', methods=['POST'])

def get_recommendations_endpoint():
    data = json.loads(request.data)
    print(data)
    doctor_id = data['doctor_id']
    max_dist = data['max_distance']
    max_members = data['max_members']

     # Call your filter_doctors function with the extracted data
    recomended_groups = get_recommendations(doctor_id, max_dist,max_members)

    # Update the response with the filtered doctors list
    response = {
        'recomended_groups': recomended_groups
    }

    # Return the response as JSON
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0')



