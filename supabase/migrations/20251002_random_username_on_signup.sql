-- Generate random username at signup
create or replace function public.random_username()
returns text as $$
declare
  adjectives text[] := array[
    'Silly','Lazy','Clumsy','Noisy','Sleepy','Fuzzy','Dizzy','Wobbly','Goofy','Kooky','Bumpy','Grumpy','Dozy','Odd','Weird','Numb','Witty','Cheeky','Quirky','Zany','Giggly','Bashful','Jumpy','Muddled','Loopy','Nifty','Nerdy','Jazzy','Wacky','Spunky','Chilly','Snarky','Zesty','Plucky','Snoozy','Peppy','Frothy','Chirpy','Perky','Wimpy'];
  animals text[] := array[
    'Donkey','Goose','Dodo','Sloth','Panda','Turkey','Lemur','Marmot','Yak','Pufferfish','Warthog','Hamster','Pigeon','Capybara','Mole','GoblinShark','Blobfish','Turtle','Cow','Sheep','Ferret','Hedgehog','Otter','Aardvark','Iguana','Koala','Platypus','Raccoon','Sardine','Giraffe','Manatee','Narwhal','Pelican','Quokka','Raven','Salamander','Tapir','Vulture','Walrus','Zebra'];
  adj text;
  animal text;
  num int;
begin
  adj := adjectives[1 + floor(random()*array_length(adjectives,1))];
  animal := animals[1 + floor(random()*array_length(animals,1))];
  num := floor(random()*100000);
  return adj || ' ' || animal || ' ' || lpad(num::text,5,'0');
end;
$$ language plpgsql volatile;

create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.app_users (id, hashed_id, email, username)
  values (new.id, new.id, new.email, public.random_username())
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
