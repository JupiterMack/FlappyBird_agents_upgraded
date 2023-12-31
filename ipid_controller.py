import numpy as np
import random
import sys
import imageio
import pygame

sys.path.append("path/to/FlappyBird_agents_upgraded")
sys.path.append("path/to/FlappyBird_environment_upgraded")
from run_ple_utils import make_ple_env

class iPIDController:
    def __init__(self, alpha, h):
        self.Kp = 1.0
        self.Kd = 1.0
        self.alpha = alpha
        self.h = h
        self.prev_error = 0
        self.prev_estimation = 0
        self.cumulative_error = 0
        self.error_threshold = 0.5

    def algebraic_estimation(self, y):
        estimation = (y - self.prev_estimation) / self.h
        self.prev_estimation = y
        return estimation

    def adjust_gains(self):
        if abs(self.cumulative_error) > self.error_threshold:
            self.Kp += 0.1
            self.Kd += 0.1
        elif abs(self.cumulative_error) < -self.error_threshold:
            self.Kp -= 0.1
            self.Kd -= 0.1

    def control_action(self, y, y_setpoint):
        error = y_setpoint - y
        self.cumulative_error += error
        d_error = (error - self.prev_error) / self.h
        d_y = self.algebraic_estimation(y)
        u = self.Kp * error + self.Kd * (d_error - self.alpha * d_y)
        self.prev_error = error
        self.adjust_gains()
        return u

    def decide_action(self, state):
        y = state[0]
        y_setpoint = 0.9 * (state[2] + state[3])
        u = self.control_action(y, y_setpoint)
        return 0 if u > 0 else 1

def main_iPID():
    # Parameters
    env_id = 'ContFlappyBird-v3'
    total_timesteps = 3000
    seed = 0
    video_path = 'C:/Users/mackj/OneDrive/Desktop/SimVids/simulation_iPID.mp4'
    image_path = 'C:/Users/mackj/OneDrive/Desktop/SimPaths/simulation_iPID_path.png'
    
    frame_interval = 71  # Capture every 71st frame

    # Performance Efficiency Score metric parameters
    time_in_gap = 0  # Counter for time spent in the gap
    total_flaps = 0  # Counter for total flaps

    test_env = make_ple_env(env_id, seed=seed)
    state = test_env.reset()
    controller = iPIDController(alpha=0.5, h=0.1)

    frames = []  # Store frames for video
    bird_positions = []  # Store the bird's positions to draw the path
    bird_safe = []
    flap_positions = []  # Store the positions where the bird flaps


    for t in range(total_timesteps):
        action = controller.decide_action(state)

        bird_y = state[0]
        gap_top = state[3]
        gap_bottom = state[2]

        # Check if the bird is in the gap
        is_safe = gap_bottom < bird_y < gap_top
        bird_safe.append(is_safe)

        if is_safe:
            time_in_gap += 1
        
        if action == 0:
            total_flaps += 1  # Increment total flaps if the bird flaps this timestep
            flap_positions.append(t)

        state, reward, done, _ = test_env.step(action)
        
        if t % frame_interval == 0:
            frame = test_env.render(mode='rgb_array')
            frame = np.flip(frame, axis=1)  # Flip horizontally
            frames.append(frame)

        # Store bird's position at every timestep
        #bird_positions.append((t * frame.shape[1] // frame_interval, int(bird_y)))  # Scale x-coordinate based on frame interval

        x_position = t * frame.shape[1] // frame_interval + 70
        bird_positions.append((x_position, int(bird_y)))

        if done:
            state = test_env.reset()


    test_env.close()

    # Combine frames and draw the path
    combined_surface = pygame.Surface((len(frames) * frames[0].shape[1], frames[0].shape[0]))

    for i, frame in enumerate(frames):
        frame_surface = pygame.surfarray.make_surface(frame).convert()
        frame_surface = pygame.transform.rotate(frame_surface, -90)  # Rotate -90 degrees
        combined_surface.blit(frame_surface, (i * frame_surface.get_width(), 0))

    # Draw the bird's path on the combined surface
    for i in range(1, len(bird_positions)):
        # Determine the color based on whether the bird was safe
        color = (0, 255, 0) if bird_safe[i] else (255, 0, 0)  # Green if safe, red otherwise
        pygame.draw.line(
            combined_surface, 
            color, 
            bird_positions[i - 1], 
            bird_positions[i], 
            5  # Width of the path
        )

    for flap_time in flap_positions:
        x_flap_position = flap_time * frame.shape[1] // frame_interval + 70
        pygame.draw.line(
            combined_surface,
            (255, 255, 255),  # White color for flap line
            (x_flap_position, 0),
            (x_flap_position, frames[0].shape[0]),
            2  # Width of the flap line
        )

    pygame.image.save(combined_surface, image_path)
    #writer = imageio.get_writer(video_path, fps=60)
    #for frame in frames:
    #    writer.append_data(frame)
    #writer.close()
    lam = 0
    PES = lam * time_in_gap / total_timesteps - (1-lam) * ( total_flaps / total_timesteps )
    print(f'Performance Efficiency Score: {PES}')


if __name__ == '__main__':
    main_iPID()
