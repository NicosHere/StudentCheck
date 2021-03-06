from studentvue import StudentVue

import datetime
import pytz

# the functions are written in the order that they are displayed on the webpage (assignments, grades, schedule)

def get_current_day():
    today = datetime.datetime.now()
    return today


# this gets the assignments for the next week

def get_days_next_week():
  today = datetime.date.today()
  days = [today]
  for i in range(1, 7):
    day = today + datetime.timedelta(days=i)
    days.append(day)
  return days

def get_upcoming_assignments(user: StudentVue):

    dates_next_week = get_days_next_week()

    assignments = user.get_calendar(
    )["CalendarListing"]["EventLists"]["EventList"]
    dates_dict = {}
    for next_date in dates_next_week:
        dates_dict[next_date] = []
        for a in assignments:
            if a["@Date"] == next_date.strftime('%m/%d/%Y'):
                dates_dict[next_date].append(a["@Title"])
        if dates_dict[next_date] == []:
          del dates_dict[next_date]
    return dates_dict


# starting getting the courses

def get_courses(user: StudentVue):
    return user.get_gradebook()['Gradebook']['Courses']['Course']

# helper functions for the grade predictions


def get_assignments(user: StudentVue):
    courses = get_courses(user)
    # user.get_gradebook()['Gradebook']['Courses']['Course'][-1]["Marks"]["Mark"]["Assignments"]["Assignment"]
    # the -1 is the course number so -1 is the last lesson

    assignments = {}
    # getting all the assignments and attaching them to their lesson name

    for course in courses:
        course_name = course["@Title"]
        
        course_assignments = []
        for a in course["Marks"]['Mark']:
          try:
            course_assignments.append(a["Assignments"]["Assignment"])
          except KeyError:
            pass
        if course_assignments != []:
          assignments[course_name] = course_assignments
        else:
          assignments[course_name] = "N/A"
    return assignments

def get_courses_with_assignments(user: StudentVue):
  assignments = get_assignments(user)
  courses_with_assignments = {}
  for key in assignments:
    if assignments[key] != "N/A":
      courses_with_assignments[key] = assignments[key]
  return courses_with_assignments

def get_weighted_assignments(user: StudentVue):
    assignments = get_assignments(user)
    graded_assignments = {}
    for lesson_name in assignments:
        lesson_grades_assignments = []
        if assignments[lesson_name] != "N/A":
            for i in assignments[lesson_name]:
                    for a in i:
                      if "not for grading" not in a["@Notes"].lower():
                          lesson_grades_assignments.append(a)
                    graded_assignments[lesson_name] = lesson_grades_assignments
        else:
            graded_assignments[lesson_name] = "N/A"
    return graded_assignments


def grade_prediction(user: StudentVue):
    assignments = get_weighted_assignments(user)

    full_scores = {}

    for key in assignments:
        earned_score = 0
        max_score = 0
        min_score = 0
        if assignments[key] != "N/A":
            for a in assignments[key]:
                a = a["@Points"]
                # this is if it is not graded
                if '/' not in a:
                    earned_points = total_points = float(a.split()[0])
                    min_points = 0
                else:
                    earned_points, total_points = a.split('/')
                    earned_points = min_points = float(earned_points)
                    total_points = float(total_points)
                earned_score += earned_points
                max_score += total_points
                min_score += min_points
                if max_score != 0 or min_score != 0:
                    max_percent = round(earned_score / max_score * 100)
                    min_percent = round(min_score / max_score * 100)
                else:
                  max_percent = min_percent = 0
                percent_dict = {"max": max_percent, "min": min_percent}
                full_scores[key] = percent_dict
        else:
            courses = get_courses(user)
            for course in courses:
                key = course["@Title"]
                value = course["Marks"]["Mark"][0]["@CalculatedScoreRaw"]
                percent_dict = {"max": value, "min": value}
                full_scores[key] = percent_dict

    return full_scores


# starting the schedule

def get_valid_schedule(user: StudentVue):
    schedule = None
    today =  user.get_schedule()["StudentClassSchedule"]["TodayScheduleInfoData"]["SchoolInfos"]
    # if there is no school today
    if today == {}:
        schedule = user.get_schedule()["StudentClassSchedule"]["ClassLists"]["ClassListing"]
    else:
        schedule = user.get_schedule()["StudentClassSchedule"]["TodayScheduleInfoData"]["SchoolInfos"]["SchoolInfo"]["Classes"]["ClassInfo"]
    return schedule

def is_holiday(user: StudentVue):
    valid_schedule = get_valid_schedule(user)
    return valid_schedule == user.get_schedule()["StudentClassSchedule"]["ClassLists"]["ClassListing"]
        

def get_current_lesson(user: StudentVue):
    if not is_holiday(user):
        schedule = get_valid_schedule(user)

        tz = pytz.timezone("America/New_York")
        current_time = datetime.datetime.now(tz).time()
        for lesson in schedule:
          start_time_str = lesson["@StartTime"]
          end_time_str = lesson["@EndTime"]
          start_in_morning = "am" in start_time_str.lower()
          end_in_morning = "am" in end_time_str.lower()

          start_time_str = start_time_str[0:-2]
          end_time_str = end_time_str[0:-2]

          start_array = start_time_str.split(":")
          end_array = end_time_str.split(":")
          
          original_start_hour = int(start_array[0]) 
          if start_in_morning:
            if original_start_hour == 12:
              start_hour = 0
            else:
              start_hour = original_start_hour
          else:
            if original_start_hour == 12:
              start_hour = 12
            else:
              start_hour = original_start_hour + 12
          

          original_end_hour = int(end_array[0])
          if end_in_morning:
            if original_end_hour == 12:
              end_hour = 0
            else:
              end_hour = original_end_hour
          else:
            if original_end_hour == 12:
              end_hour = 12
            else:
              end_hour = original_end_hour + 12
          
          
          start_minute = int(start_array[1])
          end_minute = int(end_array[1])
          start_time = datetime.time(hour=start_hour, minute=start_minute)
          end_time = datetime.time(hour=end_hour, minute=end_minute)
          
          if start_time <= current_time <= end_time:
            return lesson

    else:
        return None

