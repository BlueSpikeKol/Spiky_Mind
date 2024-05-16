# from project_memory.persistance_access import MemoryStreamAccess
#
# # Define the techniques and their descriptions
# vector_mappings = {
#     "Anticipating Consequences": """Technique: Sentiment Analysis and Predictive Modeling
# Implementation: Train a model to recognize phrases that indicate speculation about future outcomes, such as "What if" scenarios or discussions about potential problems ("if custom development exceeds the budget"). The program can use sentiment analysis to detect concern or caution, coupled with a predictive model that identifies when these concerns signal a decision-making process related to planning for potential outcomes.""",
#     "Goal Alignment": """Technique: Text Classification and Keyword Extraction
# Implementation: Implement text classification to distinguish parts of the conversation that relate to setting objectives or targets ("the goal is to have the design all wrapped up by Week 3"). Use keyword extraction to identify specific goals and timelines, allowing the program to detect when discussions align with these identified objectives, indicating a decision-making process focused on achieving set goals.""",
#     "Change or Disruption": """Technique: Topic Modeling and Change Detection Algorithms
# Implementation: Use topic modeling to understand the general themes of the conversation and detect when a shift in these themes indicates a significant change or disruption. Change detection algorithms can identify sudden deviations in the conversation's direction, such as introducing a new problem or challenge, signaling the need for a decision to adapt or respond.""",
#     "Conflict or Dissatisfaction": """Technique: Sentiment Analysis and Conflict Detection
# Implementation: Apply sentiment analysis to detect negative emotions or expressions of dissatisfaction ("the design getting too fancy for our skills"). Implement conflict detection algorithms to identify disagreements or problems within the conversation, signaling a decision point related to resolving these issues.""",
#     "Opportunity Recognition": """Technique: Named Entity Recognition (NER) and Relation Extraction
# Implementation: Use NER to identify mentions of resources, tools, or opportunities ("set aside some cash, like 50 bucks, just for design stuff"). Relation extraction can then identify connections between these entities and actions or plans, indicating a decision-making process aimed at seizing these opportunities."""
# }
#
# memory_stream = MemoryStreamAccess()
#
# # Iterate over the technique names and descriptions in the vector_mappings dictionary
# for vector_name, vector_text in vector_mappings.items():
#     memory_stream.add_to_pinecone(vector_name=vector_name, vector_text=vector_name + ". " + vector_text)

from hyphen import Hyphenator
from hyphen.dictools import *


# Define the content of the variable
var = """be – “Will you be my friend?”
and – “You and I will always be friends.”
of – “Today is the first of November.”
a – “I saw a bear today.”
in – “She is in her room.”
to – “Let’s go to the park.”
have – “I have a few questions.”
too – “I like her too.”
it – “It is sunny outside.”
I – “I really like it here.”
that – “That door is open.”
for – “This letter is for you.”
you – “You are really nice.”
he – “He is my brother.”
with – “I want to go with you.”
on – “I watch movies on my iPad.”
do – “What will you do now?”
say – “Can I say something?”
this – “This is my favorite cookie.”
they – “They are here!”
at – “Can you pick me up at the mall?”
but – “I’m sorry but she’s away.”
we – “We are going to watch a movie.”
his – “This is his box.”
from – “This card came from my cousin.”
that – “That’s a really cool trick!”
not – “That’s not what I want.”
can’t – “I can’t open it.”
won’t – “I won’t open it.”
by – “Will you come by and see me?”
she – “She is very happy.”
or – “Do you like blue or yellow?”
as – “Her role as an English teacher is very important.”
what – “What are you thinking of?”
go – “I want to go there.”
their – “This is their house.”
can – “What can I do for you?”
who – “Who can help me?”
get – “Can you get me my eyeglasses?”
if – “What if I fail?”
would – “Would you help me out?”
her – “I have her book.”
all – “All my favorite books are on this shelf.”
my – “My mom is coming to visit.”
make – “Can we make our projects together?”
about – “What is this movie about?”
know – “Do you know where this place is?”
will – “I will help you find that place.”
as – “As soon as she’s here, I’ll talk to her.”
up – “I live up in the mountains.”
one – “She is one of my English teachers.”
time – “There was a time I liked to play golf.”
there – “There are so many things I want to learn.”
year – “This is the year I’m finally going to learn English.”
so – “I am so sorry.”
think – “I think I need to lie down.”
when – “When will I see you again?”
which – “Which of these slippers are yours?”
them – “Please give this to them.”
some – “Please give them some of the apples I brought home.”
me – “Can you give me some apples?”
people – “There are so many people at the mall today.”
take – “Please take home some of these apples”
out – “Please throw the trash out.”
into – “My puppy ran into the woods.”
just – “Just close your eyes.”
see – “Did you see that?”
him – “I heard him singing earlier.”
your – “Your mom is here.”
come – “Can your mom and dad come to the party?”
could – “Could you help me with my project?”
now – “I want to watch this now.”
than – “I like this cake better than the other one you showed me.”
like – “I like this bag better than the other one you showed me.”
other – “I like these shoes better than the other ones you showed me.”
how – “How do I turn this on?”
then – “We had breakfast and then we went to church.”
its – “I need to read its manual.”
our – “This is our home now.”
two – “Two cheeseburgers, please.”
more – “Can I have some more milk shake?”
these – “Do you like these ribbons?”
want – “Do you want these ribbons?”
way – “Can you look this way?”
look – “Please look this way.”
first – “She was my very first teacher.”
also – “She was also my best friend.”
new – “I have new shoes.”
because – “I am crying because I’m sad.”
day – “Today is National Friendship day.”
more – “I have more stickers at home.”
use – “How do I use this?”
no – “There’s no electricity now.”
man – “There’s a man outside looking for you.”
find – “Where can I find rare furniture?”
here – “My mom is here.”
thing – “One thing led to another.”
give – “Give her these pearls.”
many – “We shared many dreams together.”
well – “You know me so well.”
only – “You are my only friend here.”
those – “Those boots belong to my friend.”
tell – “Can you tell me which way to go?”
one – “She’s the one he’s been waiting for.”
very – “I’m very upset right now.”
her – “Her grandmother is sick.”
even – “She can’t even stand on her own.”
back – “I’ll be right back.”
any – “Have you had any luck on your research?”
good – “You’re a good person.”
woman – “That woman looks so polished.”
through – “Your faith will see you through tough times.”
us – “Do you want to go with us?”
life – “This is the best day of my life.”
child – “I just saw a child cross the street by herself.”
there – “Did you go there?”
work – “I have to go to work.”
down – “Let’s go down.”
may – “You may take your seats.”
after – “Let’s have dinner after work.”
should – “Should I buy this dress?”
call – “Call me when you get home, okay?”
world – “I want to travel and see the world.”
over – “I can’t wait for this day to be over.”
school – “My cousin goes to school here.”
still – “I still think you should go.”
try – “Can you try to be nicer to him?”
in – “What’s in that box?”
as – “As soon as I get home, I’m going to start watching that series.”
last – “This is my last slice of cake, I promise!”
ask – “Can you ask the waiter to bring us some wine?”
need – “I need some wine tonight!”
too – “I need some wine, too!”
feel – “I feel so tired, I just need to relax and unwind.”
three – “I have three sisters.”
when – “When was the last time you saw them?”
state – “Check out the state of that shed, it’s falling apart.”
never – “I’m never going to drink wine again.”
become – “Over the years we’ve become really close.”
between – “This is just between you and me.”
high – “Give me a high five!”
really – “I really like your painting!”
something – “I have something for you.”
most – “She’s the most beautiful girl I’ve ever seen.”
another – “I’ll have another glass of wine, please.”
much – “I love you guys so much.”
family – “You are like family to me.”
own – “I want to get my own place.”
out – “Get out of my room.”
leave – “I want you to leave.”
put – “Please put down that book and listen to me.”
old – “I feel so old!”
while – “I can wait for you here while you shop.”
mean – “I didn’t mean to sound so angry.”
on – “Can you turn on the lights?”
keep – “Can we keep the lights on tonight?”
student – “I’ve always been a diligent student.”
why – “This is why I don’t go out anymore.”
let – “Why won’t you let him know how you feel?”
great – “This ice cream place is great for families with kids!”
same – “Hey, we’re wearing the same shirt!”
big – “I have this big crush on Brad Pitt.”
group – “The group sitting across our table is so noisy.”
begin – “Where do I begin with this huge project?”
seem – “She may seem quiet, but she’s really outgoing once you get to know her.”
country – “Japan is such a beautiful country!”
help – “I need help with my Math homework.”
talk – “Can we talk in private?”
where – “Where were you last night?”
turn – “If only I could turn back time.”
problem – “The problem is we think we have plenty of time.”
every – “Every person has his own big goal to fulfill.”
start – “This is a great to start to learn the English language.”
hand – “Don’t let go of my hand.”
might – “This might actually work.”
American – “The American culture is so dynamic.”
show – “Can you show me how to use this vacuum cleaner?”
part – “This is my favorite part of the movie!”
about – “What is the story about?”
against – “I am so against domestic abuse!”
place – “This place is wonderful!”
over – “She kept saying this over and over again.”
such – “He is such an annoying person.”
again – “Can we play that game again?”
few – “Just a few more errands and I’m done!”
case – “What an interesting case you are working on now!”
most – “That’s the most interesting story I’ve ever heard.”
week – “I had a rough week.”
company – “Will you keep me company?”
where – “Where are we going?”
system – “What’s wrong with the airport’s system?”
each – “Can you give each of them an apple?”
right – “I’m right this time.”
program – “This community program for teens is really helpful.”
hear – “Did you hear that?”
so – “I’m so sleepy.”
question – “I have a question for you.”
during – “During the session, I saw him fall asleep.”
work – “I have to work this weekend.”
play – “We can play soccer next weekend instead.”
government – “I hope the government does something about the poverty in this country.”
run – “If you see a bear here, run for your life.”
small – “I have a small favor to ask you.”
number – “I have a number of favors to ask you.”
off – “Please turn off the television.”
always – “I always bring pepper spray with me.”
move – “Let’s move on to the next tourist spot.”
like – “I really like you.”
night – “The night is young.”
live – “I’m going to live like there’s no tomorrow.”
Mr. – “Mr. Morris is here.”
point – “You have a point.”
believe – “I believe in you.”
hold – “Just hold my hand.”
today – “I’m going to see you today.”
bring – “Please bring a pen.”
happen – “What will happen if you don’t submit your report on time?”
next – “This is the next best thing.”
without – “I can’t live without my phone.”
before – “Before I go to bed I always wash my face.”
large – “There’s a large amount of data online about that topic.”
all – “That’s all I know about Dinosaurs.”
million – “I have a million questions about this book.”
must – “We must watch this movie together.”
home – “Can we go home now?”
under – “I hid it under my bed.”
water – “I filled the tub with water.”
room – “His room is at the end of the corridor.”
write – “Can you write me a prescription for this?”
mother – “His mother is a very lovely woman.”
area – “This area of this house needs to be fixed.”
national – “That virus has become a national concern.”
money – “She needs money to buy her medicine.”
story – “She shared her story to the media.”
young – “She is so young and so hopeful.”
fact – “It’s a fact: shopping can improve your mood.”
month – “It’s that time of the month!”
different – “Just because she’s different, it doesn’t mean she’s bad.”
lot – “You have a lot of explaining to do.”
right – “Turn right when you reach the corner.”
study – “Let’s study our English lessons together.
book – “Can I borrow your English book?”
eye – “She has the pink eye.”
job – “I love my job.”
word – “Describe yourself in one word.”
though – “Though you are angry now, I’m sure you will forget about this later.”
business – “His business is thriving.”
issue – “This is not an issue for me.”
side – “Whose side are you on, anyway?”
kind – “Always be kind, even to strangers.”
four – “There are four seasons in a year.”
head – “Let’s head back, it’s freezing out here.”
far – “We’ve gone too far and now we’re lost.”
black – “She has long, black hair.”
long – “She has long, brown hair.”
both – “They both love chocolate ice cream.”
little – “I have two little boys with me now.”
house – “The house is so quiet without you.”
yes – “I hope you say yes.”
after – “After all this time, he has finally learned to love.”
since – “Ever since his mom died, he has been cranky and angry at the world.”
long – “That was such a long time ago.”
provide – “Please provide me with a list of your services.”
service – “Do you have a specific dental service to treat this?”
around – “We went around the block.”
friend – “You’re a good friend.”
important – “You’re important to me.”
father – “My father is so important to me.”
sit – “Let’s sit outside together.”
away – “He’s away right now.”
until – “Until when will you be away?”
power – “With great power comes great responsibility.”
hour – “I’ve been checking his temperature every hour.”
game – “Let’s play a game.”
often – “I buy from his bakery as often as I can.”
yet – “He’s not yet home.”
line – “There’s a long line at the grocery cashier.”
political – “I stay away from political discussions.”
end – “It’s the end of an era.”
among – “Among all my pets, he’s my most favorite.”
ever – “Have you ever tried this cake?”
stand – “Can you stand still for a minute?”
bad – “What you did was so bad.”
lose – “I can’t lose you.”
however – “I want to buy this bag, however, I need to save up for it first.”
member – “She’s a member of the babysitter’s club.”
pay – “Let’s pay for our groceries.”
law – “There’s a law against jay-walking.”
meet – “I want you to meet my aunt.”
car – “Let’s go inside my car.”
city – “This is the city that never sleeps.”
almost – “I’m almost done with my report.”
include – “Did you remember to include the summary in your report?”
continue – “Can we continue working tomorrow?”
set – “Great, let me set an appointment for you.”
later – “I’ll finish it later.”
community – “Our community is very tight knit.”
much – “There’s so much to learn in the English language.”
name – “What’s your name?”
five – “I can give you five reasons why you need to watch that video.”
once – “I once had a puppy named Bark.”
white – “I love my white sneakers.”
least – “She’s the least productive among all the employees.”
president  – “She was our class president back in high school.”
learn – “I’d love to learn more about the English language.”
real – “What is her real name?”
change – “What can we change so that things will get better?”
team – “They hired a team to do the design of their new office.”
minute – “She’s laughing every minute of every day.”
best – “This is the best potato salad I’ve ever tasted.”
several – “I have several old clothes I need to donate.”
idea – “It was your idea to go to the beach, remember?”
kid – “I loved that toy when I was a kid.”
body – “She worked out hard to achieve a toned body.”
information – “This is the information I need.”
nothing – “There’s nothing we can do now. “
ago – “Three years ago, I visited Japan for the first time.”
right – “You’re right, I want to go back there.”
lead – “Just lead the way and I’ll follow.”
social – “I feel awkward in these social gatherings.”
understand – “I understand how you feel.”
whether – “Whether in big groups or small groups, I always feel a little shy at first.”
back – “Looking back, I knew I was always an introvert.”
watch – “Let’s watch the sun set on the horizon.”
together – “They’re together now.”
follow – “I’ll follow you home.”
around – “You’ll always have me around.”
parent – “Every parent is trying hard and doing their best.”
only – “You are only allowed to go out today.”
stop – “Please stop that.”
face – “Why is your face so red?”
anything – “You can ask me for anything.”
create – “Did you create that presentation? It was so good.”
public – “This is public property.”
already –  “I already asked him to resend his report.”
speak – “Could you speak a little louder?”
others – “The others haven’t arrived yet.”
read – “I read somewhere that this house is haunted.”
level – “What level are you in that game?”
allow – “Do you allow your kids to play outside the house?”
add – “Is it okay if we add a bit of sugar to the tea?”
office – “Welcome to my office.”
spend – “How much did you spend on your last shopping spree?”
door – “You left the door open.”
health – “You must take good care of your health.”
person – “You are a good person.”
art – “This is my work of art.”
sure – “Are you sure you want to do this alone?”
such – “You are such a brave little boy.”
war – “The war has finally ended.”
history – “She is my history professor.”
party – “Are you going to her party tonight?”
within – “We support everyone within our small community.”
grow – “We want everyone to grow and thrive in their careers.”
result – “The result of this outreach program is amazing.”
open – “Are you open to teaching on weekends?”
change – “Where can we change her diaper?”
morning – “It’s such a beautiful morning!”
walk – “Come take a walk with me.”
reason – “You are the reason I came home.”
low – “Her blood pressure has gotten really low.”
win – “We can win this match if we work together.”
research – “How is your research going?”
girl – “That girl is in my class.”
guy – “I’ve seen that guy in school before.”
early – “I come to work so early every day.”
food – “Let’s buy some food, I’m hungry!”
before – “Can I talk to you before you go home?”
moment – “The moment she walked in the room, her puppy started to jump and dance again.”
himself – “He cooked this Turkey himself.”
air – “I am loving the cold night air here.”
teacher – “You are the best teacher ever.”
force – “Don’t force him to play with other kids.”
offer – “Can I offer you a ride home?”
enough – “Boys, that’s enough playing for today.”
both – “You both need to change into your sleep clothes now.”
education – “I just want you to get the best education.”
across – “Your dog ran across the park.”
although – “Although she felt tired, she still couldn’t sleep.”
remember – “Do you think she will still remember me after ten years?”
foot – “Her foot got caught in one of the ropes.”
second – “This is the second time she got late this month.”
boy – “There’s a boy in her class who keeps pulling her hair.”
maybe – “Maybe we can have ice cream for dessert.”
toward – “He took a step toward her.”
able – “Will you be able to send me your report today?”
age – “What is the average marrying age these days?”
off – “The cat ran off with the dog.”
policy – “They have a generous return policy.”
everything – “Everything is on sale.”
love – “I love what you’re wearing!”
process – “Wait, give me time to process everything you’re telling me.”
music – “I love music.”
including – “Around 20 people attended, including Bob and Beth.”
consider – “I hope you consider my project proposal.”
appear – “How did that appear out of nowhere?”
actually – “I’m actually just heading out.”
buy – “I’m going to buy these shoes.”
probably – “He’s probably still asleep.”
human – “Give him a break, he is only human.”
wait – “Is it alright if you wait for a few minutes?”
serve – “This blow dryer has served me well for years.”
market – “Let’s visit the Sunday market.”
die – “I don’t want my cat to die, let’s take him to the vet please.”
send – “Please send the package to my address.”
expect – “You can’t expect much from their poor service.”
home – “I can’t wait to go home!”
sense – “I did sense that something was not okay.”
build – “He is going to build his dream house.”
stay – “You can stay with me for a few weeks.”
fall – “Be careful, you might fall.”
oh – “Oh no, I left my phone at home!”
nation – “We have to act as one nation.”
plan – “What’s your plan this time?”
cut – “Don’t cut your hair.”
college – “We met in college.”
interest – “Music is an interest of mine.”
death – “Death is such a heavy topic for me.”
course – “What course did you take up in college?”
someone – “Is there someone who can go with you?”
experience – “What an exciting experience!”
behind – “I’m scared to check what’s behind that door.”
reach – “I can’t reach him, he won’t answer his phone.”
local – “This is a local business.”
kill – “Smoking can kill you.”
six – “I have six books about Psychology.”
remain – “These remain on the top shelf.”
effect – “Wow, the effect of that mascara is great!”
use – “Can I use your phone?”
yeah – “Yeah, he did call me earlier.”
suggest – “He did suggest that to me.”
class – “We were in the same English class.”
control – “Where’s the remote control?”
raise – “It’s so challenging to discipline kids these days.”
care – “I don’t care about what you think.”
perhaps – “Perhaps we can arrive at a compromise.”
little – “There’s a little bird outside my window.”
late – “I am running late for my doctor’s appointment.”
hard – “That test was so hard.”
field – “He’s over there, by the soccer field.”
else – “Is anyone else coming?”
pass – “Can we pass by the grocery store?”
former – “She was my former housemate.”
sell – “We can sell your old couch online.”
major – “It’s a major issue for the project.”
sometimes – “Sometimes I forget to turn off the porch lights.”
require – “They’ll require you to show your I.D.”
along – “Can I tag along your road trip?”
development – “This news development is really interesting.”
themselves – “They can take care of themselves.”
report – “I read her report and it was great!”
role – “She’s going to play the role of Elsa.”
better – “Your singing has gotten so much better!”
economic – “Some countries are facing an economic crisis.”
effort – “The government must make an effort to solve this.”
up – “His grades have gone up.”
decide – “Please decide where to eat.”
rate – “How would you rate the hotel’s service?”
strong – “They have strong customer service here!”
possible – “Maybe it’s possible to change their bathroom amenities.”
heart – “My heart is so full.”
drug – “She got the patent for the drug she has created to cure cancer.”
show – “Can you show me how to solve this puzzle?”
leader – “You are a wonderful leader.”
light – “Watch her face light up when you mention his name.”
voice – “Hearing his mom’s voice is all he need right now.”
wife – “My wife is away for the weekend.”
whole – “I have the whole house to myself.”
police – “The police have questioned him about the incident.”
mind – “This relaxation technique really eases my mind.”
finally – “I can finally move out from my old apartment.”
pull – “My baby niece likes to pull my hair.”
return – “I give her tickles in return.”
free – “The best things in life are free.”
military – “His dad is in the military.”
price – “This is the price you pay for lying.”
report – “Did you report this to the police?”
less – “I am praying for less stress this coming new year.”
according – “According to the weather report, it’s going to rain today.”
decision – “This is a big decision for me.”
explain – “I’ll explain everything later, I promise.”
son – “His son is so cute!”
hope – “I hope I’ll have a son one day.”
even – “Even if they’ve broken up, they still remain friends.”
develop – “That rash could develop into something more serious.”
view – “This view is amazing!”
relationship – “They’ve taken their relationship to the next level.”
carry – “Can you carry my bag for me?”
town – “This town is extremely quiet.”
road – “There’s a road that leads to the edge of the woods.”
drive – “You can’t drive there, you need to walk.”
arm – “He broke his arm during practice.”
true – “It’s true, I’m leaving the company.”
federal – “Animal abuse is now a federal felony!”
break – “Don’t break the law.”
better – “You better learn how to follow rules.”
difference – “What’s the difference between happiness and contentment?”
thank – “I forgot to thank her for the pie she sent us.”
receive – “Did you receive the pie I sent you?”
value – “I value our friendship so much.”
international  – “Their brand has gone international!”
building – “This building is so tall!”
action – “You next action is going to be critical.”
full – “My work load is so full now.”
model – “A great leader is a great model of how to do things.”
join – “He wants to join the soccer team.”
season – “Christmas is my favorite season!”
society – “Their society is holding a fund raiser.”
because – “I’m going home because my mom needs me.”
tax – “How much is the current income tax?”
director – “The director yelled ‘Cut!'”
early – “I’m too early for my appointment.”
position  – “Please position your hand properly when drawing.”
player – “That basketball player is cute.”
agree – “I agree! He is cute!”
especially – “I especially like his blue eyes.”
record  – “Can we record the minutes of this meeting, please?”
pick – “Did you pick a color theme already?”
wear  – “Is that what you’re going to wear for the party?”
paper – “You can use a special paper for your invitations.”
special – “Some special paper are even scented!”
space – “Please leave some space to write down your phone number.”
ground  – “The ground is shaking.”
form – “A new island was formed after that big earthquake.”
support  – “I need your support for this project.”
event – “We’re holding a big event tonight.”
official – “Our official wedding photos are out!”
whose  – “Whose umbrella is this?”
matter – “What does it matter anyway?”
everyone  – “Everyone thinks I stole that file.”
center – “I hate being the center of attention.”
couple – “The couple is on their honeymoon now.”
site – “This site is so big!”
end – “It’s the end of an era.”
project – “This project file is due tomorrow.”
hit  – “He hit the burglar with a bat.”
base – “All moms are their child’s home base.”
activity – “What musical activity can you suggest for my toddler?”
star – “My son can draw a star!”
table  – “I saw him draw it while he was writing on the table.”
need  – “I need to enroll him to a good preschool.”
court – “There’s a basketball court near our house.”
produce  – “Fresh farm produce is the best.”
eat – “I could eat that all day.”
American – “My sister is dating an American.”
teach – “I love to teach English lessons.”
oil  – “Could you buy me some cooking oil at the store?”
half – “Just half a liter please.”
situation – “The situation is getting out of hand.”
easy – “I thought you said this was going to be easy?”
cost – “The cost of fuel has increased!”
industry – “The fuel industry is hiking prices.”
figure – “Will our government figure out how to fix this problem?”
face  – “I can’t bear to face this horrendous traffic again and again.”
street  – “Let’s cross the street.”
image – “There’s an image of him stored inside my mind.”
itself  – “The bike itself is pretty awesome.”
phone  – “Plus, it has a phone holder.”
either – “I either walk or commute to work.”
data – “How can we simplify this data?”
cover  – “Could you cover for me during emergencies?”
quite – “I’m quite satisfied with their work.”
picture  – “Picture this: a lake, a cabin, and lots of peace and quiet.
clear – “That picture is so clear inside my head.”
practice – “Let’s practice our dance number.”
piece – “That’s a piece of cake!”
land – “Their plane is going to land soon.”
recent – “This is her most recent social media post.”
describe – “Describe yourself in one word.”
product – “This is my favorite product in their new line of cosmetics.”
doctor – “The doctor is in.”
wall – “Can you post this up on the wall?”
patient  – “The patient is in so much pain now.”
worker – “She’s a factory worker.”
news  – “I saw that on the news.”
test – “I have to pass this English test.”
movie – “Let’s watch a movie later.”
certain  – “There’s a certain kind of magic in the air now.”
north – “Santa lives up north.”
love – ” l love Christmas!”
personal  – “This letter is very personal.”
open – “Why did you open and read it?”
support – “Will you support him?”
simply – “I simply won’t tolerate bad behavior.”
third – “This is the third time you’ve lied to me.”
technology – “Write about the advantages of technology.”
catch – “Let’s catch up soon, please!”
step – “Watch your step.”
baby – “Her baby is so adorable.”
computer – “Can you turn on the computer, please?”
type  – “You need to type in your password.”
attention – “Can I have your attention, please?”
draw – “Can you draw this for me?”
film – “That film is absolutely mind-blowing.”
Republican – “He is a Republican candidate.”
tree – “That tree has been there for generations.”
source – “You are my source of strength.”
red – “I’ll wear a red dress tonight.”
nearly – “He nearly died in that accident!”
organization – “Their organization is doing great things for street kids.”
choose – “Let me choose a color.”
cause – “We have to see the cause and effect of this experiment.”
hair – “I’ll cut my hair short for a change.”
look – “Can you look at the items I bought?”
point  “What is the point of all this?
century – “We’re living in the 21st century, Mary.”
evidence – “The evidence clearly shows that he is guilty.”
window  – “I’ll buy window curtains next week.”
difficult  “Sometimes, life can be difficult.”
listen – “You have to listen to your teacher.”
soon  – “I will launch my course soon.”
culture  – “I hope they understand our culture better.”
billion  – “My target is to have 1 billion dollars in my account by the end of the year.”
chance – “Is there any chance that you can do this for me?”
brother – “My brother always have my back.”
energy  –  “Now put that energy into walking.”
period – “They covered a period of twenty years.”
course  – “Have seen my course already?”
summer – “I’ll go to the beach in summer.”
less – “Sometimes, less is more.”
realize – “I just realize that I have a meeting today.”
hundred – “I have a hundred dollars that I can lend you.”
available – “I am available to work on your project.”
plant – “Plant a seed.”
likely – “It was likely a deer trail.”
opportunity – “It was the perfect opportunity to test her theory.”
term  – “I’m sure there’s a Latin term for it.”
short  – “It was just a short stay at the hotel.”
letter – “I already passed my letter of intent.”
condition – “Do you know the condition I am in?”
choice – “I have no choice.”
place – “Let’s meet out at meeting place.”
single – “I am a single parent.”
rule – “It’s the rule of the law.”
daughter – “My daughter knows how to read now.”
administration – “I will take this up with the administration.”
south – “I am headed south.”
husband – “My husband just bought me a ring for my birthday.”
Congress – “It will be debated at the Congress.”
floor – “She is our floor manager.”
campaign – “I handled their election campaign.”
material – “She had nothing material to report.”
population – “The population of the nearest big city was growing.”
well – “I wish you well.”
call – ” I am going to call the bank.”
economy – “The economy is booming.”
medical -“She needs medical assistance.”
hospital – “I’ll take her to the nearest hospital.”
church  – “I saw you in church last Sunday.”
close -“Please close the door.”
thousand – “There are a thousand reasons to learn English!”
risk – “Taking a risk can be rewarding.”
current – “What is your current address?”
fire – “Make sure your smoke alarm works in case of fire.”
future  -“The future is full of hope.”
wrong – “That is the wrong answer.”
involve – “We need to involve the police.”
defense – “What is your defense or reason you did this?”
anyone – “Does anyone know the answer?”
increase – “Let’s increase your test score.”
security – “Some apartment buildings have security.”
bank – “I need to go to the bank to withdraw some money.”
myself – “I can clean up by myself.”
certainly – “I can certainly help clean up.”
west – “If you drive West, you will arrive in California.”
sport – “My favorite sport is soccer.”
board – “Can you see the board?”
seek – “Seek and you will find.”
per – “Lobster is $20 per pound.”
subject – “My favorite subject is English!”
officer – “Where can I find a police officer?”
private – “This is a private party.”
rest – “Let’s take a 15 minute rest.”
behavior – “This dog’s behavior is excellent.”
deal – “A used car can be a good deal.”
performance – “Your performance can be affected by your sleep.”
fight – “I don’t want to fight with you.”
throw – “Throw me the ball!”
top – “You are a top student.”
quickly – “Let’s finish reading this quickly.”
past – “In the past, my English was not as good as it is today.”
goal – “My goal is to speak English fluently.”
second – “My second goal is to increase my confidence.”
bed – “I go to bed around 10pm.”
order – “I would like to order a book.”
author – “The author of this series is world-famous.”
fill – “I need to fill (up) my gas tank.”
represent – “I represent my family.”
focus – “Turn off your phone and the TV and focus on your studies!”
foreign – “It’s great having foreign friends.”
drop – “Please don’t drop the eggs!”
plan – “Let’s make a plan.”
blood – “The hospital needs people to give blood.”
upon – “Once upon a time, a princess lived in a castle.”
agency – “Let’s contract an agency to help with marketing.”
push – “The door says ‘push,’ not ‘pull.'”
nature – “I love walking in nature!”
color – “My favorite color is blue.”
no – “‘No’ is one of the shortest complete sentences.”
recently – “I cleaned the bathroom most recently, so I think it’s your turn this time.”
store – “I’m going to the store to buy some bread.”
reduce – “Reduce, reuse, and recycle are the ways to help the environment.”
sound – “I like the sound of wind chimes.”
note – “Please take notes during the lesson.”
fine – “I feel fine.”
before – “Before the movie, let’s buy popcorn!”
near – “Near, far, wherever you are, I do believe that the heart goes on.”
movement – “The environmental movement is an international movement.”
page – “Please turn to page 62.”
enter – “You can enter the building on the left.”
share – “Let me share my idea.”
than – “Ice cream has more calories than water.”
common – “Most people can find something in common with each other.”
poor – “We had a poor harvest this year because it was so dry.”
other  – “This pen doesn’t work, try the other one.”
natural – “This cleaner is natural, there aren’t any chemicals in it.”
race – “We watched the car race on TV.”
concern – “Thank you for your concern, but I’m fine.”
series – “What is your favorite TV series?”
significant – “His job earns a significant amount of money.”
similar – “These earrings don’t match, but they are similar.”
hot – “Don’t touch the stove, it’s still hot.”
language – “Learning a new language is fun.”
each – “Put a flower in each vase.”
usually – “I usually shop at the corner store.”
response – “I didn’t expect his response to come so soon.”
dead – “My phone is dead, let me charge it.”
rise – “The sun will rise at 7:00 a.m.”
animal – “What kind of animal is that?”
factor – “Heredity is a factor in your overall health.”
decade – “I’ve lived in this city for over a decade.”
article – “Did you read that newspaper article?”
shoot – “He wants to shoot arrows at the target.”
east – “Drive east for three miles.”
save – “I save all my cans for recycling.”
seven – “There are seven slices of pie left.”
artist – “Taylor Swift is a recording artist.”
away – “I wish that mosquito would go away.”
scene – “He painted a colorful street scene.”
stock – “That shop has a good stock of postcards.”
career – “Retail sales is a good career for some people.”
despite – “Despite the rain, we will still have the picnic.”
central – “There is good shopping in central London.”
eight – “That recipe takes eight cups of flour.”
thus – “We haven’t had any problems thus far.”
treatment – “I will propose a treatment plan for your injury.”
beyond – “The town is just beyond those mountains.”
happy – “Kittens make me happy.”
exactly – “Use exactly one teaspoon of salt in that recipe.”
protect – “A coat will protect you from the cold weather.”
approach – “The cat slowly approached the bird.”
lie – “Teach your children not to lie.”
size – “What size is that shirt?
dog – “Do you think a dog is a good pet?”
fund – “I have a savings fund for college.”
serious – “She is so serious, she never laughs.”
occur – “Strange things occur in that empty house.”
media – “That issue has been discussed in the media.”
ready – “Are you ready to leave for work?”
sign – “That store needs a bigger sign.”
thought – “I’ll have to give it some thought.”
list – “I made a list of things to do.”
individual – “You can buy an individual or group membership.”
simple – “The appliance comes with simple instructions.”
quality – “I paid a little more for quality shoes.”
pressure – “There is no pressure to finish right now.”
accept – “Will you accept my credit card?”
answer – “Give me your answer by noon tomorrow.”
hard – “That test was very hard.”
resource – “The library has many online resources.”
identify – “I can’t identify that plant.”
left – “The door is on your left as you approach.”
meeting – “We’ll have a staff meeting after lunch.”
determine – “Eye color is genetically determined.”
prepare – “I’ll prepare breakfast tomorrow.”
disease – “Face masks help prevent disease.”
whatever – “Choose whatever flavor you like the best.”
success – “Failure is the back door to success.”
argue – “It’s not a good idea to argue with your boss.”
cup – “Would you like a cup of coffee?”
particularly – “It’s not particularly hot outside, just warm.”
amount – “It take a large amount of food to feed an elephant.”
ability – “He has the ability to explain things well.”
staff – “There are five people on staff here.”
recognize – “Do you recognize the person in this photo?”
indicate – “Her reply indicated that she understood.”
character – “You can trust people of good character.”
growth – “The company has seen strong growth this quarter.”
loss – “The farmer suffered heavy losses after the storm.”
degree – “Set the oven to 300 degrees.”
wonder – “I wonder if the Bulls will win the game.”
attack – “The army will attack at dawn.”
herself – “She bought herself a new coat.”
region – “What internet services are in your region?”
television – “I don’t watch much television.”
box – “I packed my dishes in a strong box.”
TV – “There is a good movie on TV tonight.”
training – “The company will pay for your training.”
pretty – “That is a pretty dress.”
trade – “The stock market traded lower today.”
deal – “I got a good deal at the store.”
election – “Who do you think will win the election?”
everybody – “Everybody likes ice cream.”
physical – “Keep a physical distance of six feet.”
lay – “Lay the baby in her crib, please.”
general – “My general impression of the restaurant was good.”
feeling – “I have a good feeling about this.”
standard – “The standard fee is $10.00.”
bill – “The electrician will send me a bill.”
message – “You have a text message on your phone.”
fail – “I fail to see what is so funny about that.”
outside – “The cat goes outside sometimes.”
arrive – “When will your plane arrive?”
analysis – “I’ll give you my analysis when I’ve seen everything.”
benefit – “There are many health benefits to quinoa.”
name – “What’s your name?”
sex – “Do you know the sex of your baby yet?”
forward – “Move the car forward a few feet.”
lawyer – “My lawyer helped me write a will.”
present – “If everyone is present, the meeting can begin.”
section – “What section of the stadium are you sitting in?”
environmental – “Environmental issues are in the news.”
glass – “Glass is much heavier than plastic.”
answer – “Could you answer a question for me?”
skill – “His best skill is woodworking.”
sister – “My sister lives close to me.”
PM – “The movie starts at 7:30 PM.”
professor – “Dr. Smith is my favorite professor.”
operation – “The mining operation employs thousands of people.”
financial – “I keep my accounts at my financial institution.”
crime – “The police fight crime.”
stage – “A caterpillar is the larval stage of a butterfly.”
ok – “Would it be ok to eat out tonight?”
compare – “We should compare cars before we buy one.”
authority – “City authorities make the local laws.”
miss – “I miss you, when will I see you again?”
design – “We need to design a new logo.”
sort – “Let’s sort these beads according to color.”
one – “I only have one cat.”
act – “I’ll act on your information today.”
ten – “The baby counted her ten toes.”
knowledge – “Do you have the knowledge to fix that?”
gun – “Gun ownership is a controversial topic.”
station – “There is a train station close to my house.”
blue – “My favorite color is blue.”
state – “After the accident I was in a state of shock.”
strategy – “Our new corporate strategy is written here.”
little – “I prefer little cars.”
clearly – “The instructions were clearly written.”
discuss – “We’ll discuss that at the meeting.”
indeed – “Your mother does indeed have hearing loss.”
force – “It takes a lot of force to open that door.”
truth – “Please tell me the truth.”
song – “That’s a beautiful song.”
example – “I need an example of that grammar point, please.”
democratic – “Does Australia have a democratic government?”
check – “Please check my work to be sure it’s correct.”
environment – “We live in a healthy environment.”
leg – “The boy broke his leg.”
dark – “Turn on the light, it’s dark in here.”
public – “Masks must be worn in public places.”
various – “That rug comes in various shades of gray.”
rather – “Would you rather have a hamburger than a hot dog?”
laugh – “That movie always makes me laugh.”
guess – “If you don’t know, just guess.”
executive – “The company’s executives are paid well.”
set – “Set the glass on the table, please.”
study – “He needs to study for the test.”
prove – “The employee proved his worth.”
hang – “Please hang your coat on the hook.”
entire – “He ate the entire meal in 10 minutes.”
rock – “There are decorative rocks in the garden.”
design – “The windows don’t open by design.”
enough – “Have you had enough coffee?”
forget – “Don’t forget to stop at the store.”
since – “She hasn’t eaten since yesterday.”
claim – “I made an insurance claim for my car accident.”
note – “Leave me a note if you’re going to be late.”
remove – “Remove the cookies from the oven.”
manager – “The manager will look at your application.”
help – “Could you help me move this table?”
close – “Close the door, please.”
sound – “The dog did not make a sound.”
enjoy – “I enjoy soda.”
network – “Band is the name of our internet network.”
legal – “The legal documents need to be signed.”
religious – “She is very religious, she attends church weekly.”
cold – “My feet are cold.”
form – “Please fill out this application form.”
final – “The divorce was final last month.”
main – “The main problem is a lack of money.”
science – “He studies health science at the university.”
green – “The grass is green.”
memory – “He has a good memory.”
card – “They sent me a card for my birthday.”
above – “Look on the shelf above the sink.”
seat – “That’s a comfortable seat.”
cell – “Your body is made of millions of cells.”
establish – “They established their business in 1942.”
nice – “That’s a very nice car.”
trial – “They are employing her on a trial basis.”
expert – “Matt is an IT expert.”
that – “Did you see that movie?”
spring – “Spring is the most beautiful season.”
firm – “Her ‘no” was very firm, she won’t change her mind.”
Democrat – “The Democrats control the Senate.”
radio – “I listen to the radio in the car.”
visit – “We visited the museum today.”
management – “That store has good management.”
care – “She cares for her mother at home.”
avoid – “You should avoid poison ivy.”
imagine – “Can you imagine if pigs could fly?”
tonight – “Would you like to go out tonight?”
huge – “That truck is huge!”
ball – “He threw the ball to the dog.”
no – “I said ‘no,’ please don’t ask again.”
close – “Close the window, please.”
finish – “Did you finish your homework?”
yourself – “You gave yourself a haircut?”
talk – “He talks a lot.”
theory – “In theory, that’s a good plan.”
impact – “The drought had a big impact on the crops.”
respond – “He hasn’t responded to my text yet.”
statement – “The police chief gave a statement to the media.”
maintain – “Exercise helps you maintain a healthy weight.”
charge – “I need to charge my phone.”
popular – “That’s a popular restaurant.”
traditional – “They serve traditional Italian food there.”
onto – “Jump onto the boat and we’ll go fishing.”
reveal – “Washing off the dirt revealed the boy’s skinned knee.”
direction – “What direction is the city from here?”
weapon – “No weapons are allowed in government buildings.”
employee – “That store only has three employees.”
cultural – “There is cultural significance to those old ruins.”
contain – “The carton contains a dozen egges.”
peace – “World leaders gathered for peace talks.”
head – “My head hurts.”
control – “Keep control of the car.”
base – “The glass has a heavy base so it won’t fall over.”
pain – “I have chest pain.”
apply – “Maria applied for the job.”
play – “The children play at the park.”
measure – “Measure twice, cut once.”
wide – “The doorway was very wide.”
shake – “Don’t shake the can of soda.”
fly – “We can fly to France next year.”
interview – “My job interview went well.”
manage – “Did you manage to find the keys?”
chair – “The table has six matching chairs.”
fish – “I don’t enjoy eating fish.”
particular – “That particular style looks good on you.”
camera – “I use the camera on my phone.”
structure – “The building’s structure is solid.”
politics – “Mitch is very active in politics.”
perform – “The singer will perform tonight.”
bit – “It rained a little bit last night.”
weight – “Keep track of your pet’s weight.”
suddenly – “The storm came up suddenly.”
discover – “You’ll discover treasures at that thrift store.”
candidate – “There are ten candidates for the position.”
top – “The flag flies on the top of that building.”
production – “Factory production has improved over the summer.”
treat – “Give yourself a treat for a job well done.”
trip – “We are taking a trip to Florida in January.”
evening – “I’m staying home this evening.”
affect – “My bank account will affect how much I can buy.”
inside – “The cat stays inside.”
conference – “There will be expert presenters at the conference.”
unit – “A foot is a unit of measure.”
best – “Those are the best glasses to buy.”
style – “My dress is out of style.”
adult – “Adults pay full price, but children are free.”
worry – “Don’t worry about tomorrow.”
range – My doctor offered me a range of options.
mention – “Can you mention me in your story?”
rather – “Rather than focusing on the bad things, let’s be grateful for the good things.”
far – “I don’t want to move far from my family.”
deep – “That poem about life is deep.”
front – “Please face front.”
edge – “Please do not stand so close to the edge of the cliff.”
individual – “These potato chips are in an individual serving size package.”
specific – “Could you be more specific?”
writer – “You are a good writer.”
trouble – “Stay out of trouble.”
necessary – “It is necessary to sleep.”
throughout – “Throughout my life I have always enjoyed reading.”
challenge – “I challenge you to do better.”
fear – “Do you have any fears?”
shoulder – “You do not have to shoulder all the work on your own.”
institution – “Have you attended any institution of higher learning?”
middle – “I am a middle child with one older brother and one younger sister.”
sea – “I want to sail the seven seas.”
dream – “I have a dream.”
bar – “A bar is a place where alcohol is served.”
beautiful – “You are beautiful.”
property – “Do you own property, like a house?”
instead – “Instead of eating cake I will have fruit.”
improve – “I am always looking for ways to improve.”
stuff – “When I moved, I realized I have a lot of stuff!”
claim – “I claim to be a fast reader, but actually I am average.”"""

lines = var.split('\n')

# Initialize a dictionary to store syllables and all the words they appear in
syllable_sources = {}

# Check if the dictionary is available, and install it if not
language = 'en_US'
if not is_installed(language):
    install(language)

# Create a Hyphenator instance
hyphenator = Hyphenator(language)

# Function to dismantle a word into syllables and map to their source word
def add_syllables(word):
    syllables = hyphenator.syllables(word)
    # Only map syllables if there's more than one (decomposed)
    if len(syllables) > 1:
        for syllable in syllables:
            if syllable in syllable_sources:
                syllable_sources[syllable].add(word)
            else:
                syllable_sources[syllable] = {word}

# Process each line
for index, line in enumerate(lines, start=1):
    try:
        word, description = line.split(' – ')
        word = word.strip()
        add_syllables(word)
    except ValueError as e:
        print(f"Skipping line {index} due to error: {e}")

# Sort all syllables alphabetically
sorted_syllables = sorted(syllable_sources.keys())

# Output all syllables collected and sorted, with their source words, each printed once
print("Syllables (sorted alphabetically) and their source words:")
output = []
for syllable in sorted_syllables:
    sources = syllable_sources[syllable]
    source_words = ', '.join(sources)
    output.append(f"{syllable} (from '{source_words}')")
print(", ".join(output))
print("Total number of syllables (printed once):", len(sorted_syllables))

# Optionally, output repeated syllables and their counts
print("Repeated syllables and the number of words they appear in:")
for syllable, sources in sorted(syllable_sources.items()):
    if len(sources) > 1:
        print(f"{syllable} appears in {len(sources)} words")

import spacy

# Assuming nlp model is loaded, if not, uncomment the next line to load it
nlp = spacy.load("en_core_web_lg")

# New text to process
new_text = """THE SMARTEST MAN IS HARD TO FIND
Dom DeLuise, celebrity fat man (and five of clubs), has been implicated in the following
unseemly acts in my mind’s eye: He has hocked a fat globule of spittle (nine of clubs) on Albert Einstein’s thick white mane (three of diamonds) and delivered a devastating karate kick
(five of spades) to the groin of Pope Benedict XVI (six of diamonds). Michael Jackson (king of
hearts) has engaged in behavior bizarre even for him. He has defecated (two of clubs) on a
salmon burger (king of clubs) and captured his flatulence (queen of clubs) in a balloon (six of
spades). Rhea Perlman, diminutive Cheers bartendress (and queen of spades), has been
caught cavorting with the seven-foot-seven Sudanese basketball star Manute Bol (seven of
clubs) in a highly explicit (and in this case, anatomically improbable) two-digit act of congress
(three of clubs).
This tawdry tableau, which I’m not proud to commit to the page, goes a long way toward
explaining the unlikely spot I find myself in at the moment. Sitting to my left is Ram Kolli, an
unshaven twenty-five-year-old business consultant from Richmond, Virginia, who is also the
defending United States memory champion. To my right is the muzzle of a television camera
from a national cable network. Spread out behind me, where I can’t see them and they can’t
disturb me, are about a hundred spectators and a pair of TV commentators offering play-byplay analysis. One is a blow-dried veteran boxing announcer named Kenny Rice, whose gravelly, bedtime voice can’t conceal the fact that he seems bewildered by this jamboree of nerds.
The other is the Pelé of U.S. memory sport, a bearded forty-three-year-old chemical engineer
and four-time national champion from Fayetteville, North Carolina, named Scott Hagwood. In
the corner of the room sits the object of my affection: a kitschy two-tiered trophy consisting of
a silver hand with gold nail polish brandishing a royal flush, and, in a patriotic flourish, three
bald eagles perched just below. It’s nearly as tall as my two-year-old niece (and lighter than
most of her stuffed animals).
The audience has been asked not to take any flash photographs and to maintain total silence. Not that Ram or I could possibly hear them. Both of us are wearing earplugs. I’ve also
got on a pair of industrialstrength earmuffs that look like they belong on an aircraft carrier
deckhand (because in the heat of a memory competition, there is no such thing as deaf
enough). My eyes are closed. On a table in front of me, lying facedown between my hands,
are two shuffled decks of playing cards. In a moment, the chief arbiter will click a stopwatch
and I will have five minutes to memorize the order of both decks.
The unlikely story of how I ended up in the finals of the U.S. Memory Championship,
stock-still and sweating profusely, begins a year earlier on a snowy highway in central
Pennsylvania. I had been driving from my home in Washington, D.C., to the Lehigh Valley to
do an interview for Discover magazine with a theoretical physicist at Kutztown University, who
had invented a vacuum chamber device that was supposed to pop the world’s largest popcorn. My route took me through York, Pennsylvania, home of the Weightlifting Hall of Fame
and Museum. I thought that sounded like something I didn’t want to die without having seen.
And I had an hour to kill.
As it turned out, the Hall of Fame was little more than a sterile collection of old photographs and memorabilia displayed on the ground floor of the corporate offices of the nation’s
largest barbell manufacturer. Museologically, it was crap. But it’s where I first saw a blackand-white photo of Joe “The Mighty Atom” Greenstein, a hulking five-foot-four Jewish-American strongman who had earned his nickname in the 1920s by performing such inspiring feats as biting quarters in half and lying on a bed of nails while a fourteen-man Dixieland band played on his chest. He once changed all four tires on a car without any tools. A
caption next to the photo billed Greenstein as “the strongest man in the world.”
Staring at that photo, I thought it would be pretty interesting if the world’s strongest person
ever got to meet the world’s smartest person. The Mighty Atom and Einstein, arms wrapped
around each other: an epic juxtaposition of muscle and mind. A neat photo to hang above my
desk, at least. I wondered if it had ever been taken. When I got home, I did a little Googling.
The world’s strongest person was pretty easy to find: His name was Mariusz Pudzianowski.
He lived in Biaa Rawska, Poland, and could deadlift 924 pounds (about thirty of my nieces).
The world’s smartest person, on the other hand, was not so easily identified. I typed in
“highest IQ,” “intelligence champion,” “smartest in the world.” I learned that there was
someone in New York City with an IQ of 228, and a chess player in Hungary who once
played fifty-two simultaneous blindfolded games. There was an Indian woman who could calculate the twenty-third root of a two-hundred-digit number in her head in fifty seconds, and
someone else who could solve a fourdimensional Rubik’s cube, whatever that is. And of
course there were plenty of more obvious Stephen Hawking types of candidates. Brains are
notoriously trickier to quantify than brawn.
In the course of my Googling, though, I did discover one intriguing candidate who was, if
not the smartest person in the world, at least some kind of freakish genius. His name was Ben
Pridmore, and he could memorize the precise order of 1,528 random digits in an hour and—to
impress those of us with a more humanist bent—any poem handed to him. He was the reigning world memory champion.
Over the next few days, my brain kept returning to Ben Pridmore’s. My own memory was
average at best. Among the things I regularly forgot: where I put my car keys (where I put my
car, for that matter); the food in the oven; that it’s “its” and not “it’s”; my girlfriend’s birthday,
our anniversary, Valentine’s Day; the clearance of the doorway to my parents’ cellar (ouch);
my friends’ phone numbers; why I just opened the fridge; to plug in my cell phone; the name
of President Bush’s chief of staff; the order of the New Jersey Turnpike rest stops; which year
the Redskins last won the Super Bowl; to put the toilet seat down.
Ben Pridmore, on the other hand, could memorize the order of a shuffled deck of playing
cards in thirty-two seconds. In five minutes he could permanently commit to memory what
happened on ninety-six different historical dates. The man knew fifty thousand digits of pi.
What was not to envy? I had once read that the average person squanders about forty days a
year compensating for things he or she has forgotten. Putting aside for a moment the fact that
he was temporarily unemployed, how much more productive must Ben Pridmore be?
Every day there seems to be more to remember: more names, more passwords, more appointments. With a memory like Ben Pridmore’s, I imagined, life would be qualitatively different—and better. Our culture constantly inundates us with new information, and yet our brains
capture so little of it. Most just goes in one ear and out the other. If the point of reading were
simply to retain knowledge, it would probably be the single least efficient activity I engage in. I
can spend a half dozen hours reading a book and then have only a foggy notion of what it
was about. All those facts and anecdotes, even the stuff interesting enough to be worth underlining, have a habit of briefly making an impression on me and then disappearing into who
knows where. There are books on my shelf that I can’t even remember whether I’ve read or
not.
What would it mean to have all that otherwise-lost knowledge at my fingertips? I couldn’t
help but think that it would make me more persuasive, more confident, and, in some fundamental sense, smarter. Certainly I’d be a better journalist, friend, and boyfriend. But more
than that, I imagined that having a memory like Ben Pridmore’s would make me an altogether
more attentive, perhaps even wiser, person. To the extent that experience is the sum of our
memories and wisdom the sum of experience, having a better memory would mean knowing
not only more about the world, but also more about myself. Surely some of the forgetting that
seems to plague us is healthy and necessary. If I didn’t forget so many of the dumb things I’ve
done, I’d probably be unbearably neurotic. But how many worthwhile ideas have gone unthought and connections unmade because of my memory’s shortcomings?
I kept returning to something Ben Pridmore said in a newspaper interview, which made
me ponder just how different his memory and my own might really be. “It’s all about technique
and understanding how the memory works,” he told the reporter. “Anyone could do it, really.”
A couple weeks after my trip to the Weightlifting Hall of Fame, I stood in the back of an
auditorium on the nineteenth floor of the Con Edison headquarters near Union Square in
Manhattan, an observer at the 2005 U.S. Memory Championship. Spurred by my fascination
with Ben Pridmore, I was there to write a short piece for Slate magazine about what I imagined would be the Super Bowl of savants.
The scene I stumbled on, however, was something less than a clash of titans: a bunch of
guys (and a few ladies), widely varying in both age and hygienic upkeep, poring over pages of
random numbers and long lists of words. They referred to themselves as “mental athletes,” or
just MAs for short.
There were five events. First the contestants had to learn by heart a fifty-line unpublished
poem called “The Tapestry of Me.” Then they were provided with ninety-nine photographic
head shots accompanied by first and last names and given fifteen minutes to memorize as
many of them as possible. Then they had another fifteen minutes to memorize a list of three
hundred random words, five minutes to memorize a page of a thousand random digits
(twenty-five lines of numbers, forty numbers to a line), and another five minutes to learn the
order of a shuffled deck of playing cards. Among the competitors were two of the world’s
thirty-six grand masters of memory, a rank attained by memorizing a sequence of a thousand
random digits in under an hour, the precise order of ten shuffled decks of playing cards in the
same amount of time, and the order of one shuffled deck in less than two minutes.
Though on the face of it these feats might seem like little more than geeky party
tricks—essentially useless, and perhaps even vaguely pathetic—what I discovered as I talked
to the competitors was something far more serious, a story that made me reconsider the limits
of my own mind and the very essence of my education.
I asked Ed Cooke, a young grand master from England who had come to the U.S. event
as spring training for that summer’s World Championship (since he was a non-American, his
scores couldn’t be counted in the U.S. contest), when he first realized he was a savant.
“Oh, I’m not a savant,” he said, chuckling.
“Photographic memory?” I asked.
He chuckled again. “Photographic memory is a detestable myth,” he said. “Doesn’t exist.
In fact, my memory is quite average. All of us here have average memories.”
That seemed hard to square with the fact that I’d just watched him recite back 252 random
digits as effortlessly as if they’d been his own telephone number.
“What you have to understand is that even average memories are remarkably powerful if
used properly,” he said. Ed had a blocky face and a shoulder-length mop of curly brown hair,
and could be counted among the competitors who were least concerned with habits of personal grooming. He was wearing a suit with a loosened tie and, incongruously, a pair of flip-
flops emblazoned with the Union Jack. He was twenty-four years old but carried his body like
someone three times that age. He hobbled about with a cane at his side—“a winning prop,”
he called it—which was necessitated by a recent painful relapse of chronic juvenile arthritis.
He and all the other mental athletes I met kept insisting, as Ben Pridmore had in his interview,
that anyone could do what they do. It was simply a matter of learning to “think in more memorable ways” using the “extraordinarily simple” 2,500-year-old mnemonic technique known as
the “memory palace” that Simonides of Ceos had supposedly invented in the rubble of the
great banquet hall collapse.
The techniques of the memory palace—also known as the journey method or the method
of loci, and more broadly as the ars memorativa, or “art of memory”—were refined and codified in an extensive set of rules and instruction manuals by Romans like Cicero and Quintilian, and flowered in the Middle Ages as a way for the pious to memorize everything from sermons and prayers to the punishments awaiting the wicked in hell. These were the same tricks
that Roman senators had used to memorize their speeches, that the Athenian statesman
Themistocles had supposedly used to memorize the names of twenty thousand Athenians,
and that medieval scholars had used to memorize entire books.
Ed explained to me that the competitors saw themselves as “participants in an amateur research program” whose aim was to rescue a long-lost tradition of memory training that had
disappeared centuries ago. Once upon a time, Ed insisted, remembering was everything. A
trained memory was not just a handy tool, but a fundamental facet of any worldly mind.
What’s more, memory training was considered a form of character building, a way of developing the cardinal virtue of prudence and, by extension, ethics. Only through memorizing, the
thinking went, could ideas truly be incorporated into one’s psyche and their values absorbed.
The techniques existed not just to memorize useless information like decks of playing cards,
but also to etch into the brain foundational texts and ideas.
But then, in the fifteenth century, Gutenberg came along and turned books into massproduced commodities, and eventually it was no longer all that important to remember what
the printed page could remember for you. Memory techniques that had once been a staple of
classical and medieval culture got wrapped up with the occult and esoteric Hermetic traditions
of the Renaissance, and by the nineteenth century they had been relegated to carnival
sideshows and tacky self-help books—only to be resurrected in the last decades of the twentieth century for this bizarre and singular competition.
The leader of this renaissance in memory training is a slick sixty-seven-year-old British
educator and self-styled guru named Tony Buzan, who claims to have the highest “creativity
quotient” in the world. When I met him, in the cafeteria of the Con Edison building, he was
wearing a navy suit with five enormous gold-rimmed buttons and a collarless shirt, with anoth-
er large button at his throat that gave him the air of an Eastern priest. A neuron-shaped pin
adorned his lapel. His watch face bore a reproduction of Dali’s Persistence of Memory (the
one with the dripping watch face). He referred to the competitors as “warriors of the mind.”
Buzan’s grizzled face looked a decade older than his sixty-seven years, but the rest of him
was as trim as a thirty-year-old. He rows between six and ten kilometers every morning on the
river Thames, he told me, and he makes a point of eating lots of “brain-healthy” vegetables
and fish. “Junk food in: junk brain. Healthy food in: healthy brain,” he said.
When he walked, Buzan seemed to glide across the floor like an air hockey puck (the result, he later told me, of forty years’ training in the Alexander Technique). When he spoke, he
gesticulated with a polished, staccato precision that could only have been honed in front of a
mirror. Often, he punctuated a key point with an explosion of fingers from his closed fist.
Buzan founded the World Memory Championship in 1991 and has since established national championships in more than a dozen countries, from China to South Africa to Mexico.
He says he has been working with a missionary’s zeal since the 1970s to get these memory
techniques implemented in schools around the world. He calls it a “global education revolution
focusing on learning how to learn.” And he’s been minting himself a serious fortune in the process. (According to press reports, Michael Jackson ran up a $343,000 bill for Buzan’s mindboosting services shortly before his death.)
Buzan believes schools go about teaching all wrong. They pour vast amounts of information into students’ heads, but don’t teach them how to retain it. Memorizing has gotten a bad
rap as a mindless way of holding onto facts just long enough to pass the next exam. But it’s
not memorization that’s evil, he says; it’s the tradition of boring rote learning that he believes
has corrupted Western education. “What we have been doing over the last century is defining
memory incorrectly, understanding it incompletely, applying it inappropriately, and condemning it because it doesn’t work and isn’t enjoyable,” Buzan argues. If rote memorization is
a way of scratching impressions onto our brains through the brute force of repetition—the old
“drill and kill” method—then the art of memory is a more elegant way of remembering through
technique. It is faster, less painful, and produces longerlasting memories, Buzan told me.
“The brain is like a muscle,” he said, and memory training is a form of mental workout.
Over time, like any form of exercise, it’ll make the brain fitter, quicker, and more nimble. It’s an
idea that dates back to the very origins of memory training. Roman orators argued that the art
of memory—the proper retention and ordering of knowledge—was a vital instrument for the
invention of new ideas. Today, the “mental workout” has gained great currency in the popular
imagination. Brain gyms and memory boot camps are a growing fad, and brain training software was a $265 million industry in 2008, no doubt in part because of research that shows
that older people who keep their minds active with crossword puzzles and chess can stave off
Alzheimer’s and progressive dementia, but mostly because of the Baby Boomer generation’s
intense insecurity about losing their marbles."""

# Tokenize the new text
doc = nlp(new_text)

# Variables to track unmatched words and syllables
unmatched_words = []
total_unmatched_syllables = 0
unmatched_syllable_details = {}  # To store unmatched syllables and their corresponding words

# Function to check syllables in new text
def check_syllables(word):
    syllables = hyphenator.syllables(word)
    if len(syllables) > 1:  # Only consider words that can be decomposed
        unmatched_syllables = [syl for syl in syllables if syl not in syllable_sources]
        if unmatched_syllables:
            unmatched_words.append(word)
            for syl in unmatched_syllables:
                if syl in unmatched_syllable_details:
                    unmatched_syllable_details[syl].add(word)
                else:
                    unmatched_syllable_details[syl] = {word}
            return len(unmatched_syllables)
    return 0

# Process each token in the new text
for token in doc:
    if token.is_alpha:  # Check only alphabetical words
        unmatched_count = check_syllables(token.text.lower())
        total_unmatched_syllables += unmatched_count

# Print the results
if unmatched_words:
    print("Words with syllables not found in the common list:")
    for word in unmatched_words:
        print(word)
    print(f"Total number of words with unmatched syllables: {len(unmatched_words)}")
    print(f"Total number of unmatched syllables: {total_unmatched_syllables}")

    print("\nUnmatched syllables and their words:")
    for syl, words in unmatched_syllable_details.items():
        print(f"Syllable '{syl}' not matched, found in words: {', '.join(words)}")
else:
    print("All syllables in the text matched the common syllable list.")



