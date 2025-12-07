import pandas as pd
import bar_chart_race as bcr
import os
import matplotlib.pyplot as plt

def animate():
    if not os.path.exists('f1_2025_cumulative_standings.csv'):
        print("Data file not found. Please wait for fetch_data.py to complete.")
        return

    print("Loading data...")
    df = pd.read_csv('f1_2025_cumulative_standings.csv', index_col='Round')
    
    # Ensure index is sorted
    df.sort_index(inplace=True)
    
    # Fill NaN with previous values (ffill) just in case, though cumsum should handle it.
    # Actually, 0 fill was done before cumsum.
    
    print("Generating animation... this may take a minute.")
    
    # Custom colors mapping? Need valid matplotlib colors.
    # Using default colors for now.
    
    try:
        bcr.bar_chart_race(
            df=df,
            filename='f1_2025_standings.mp4',
            orientation='h',
            sort='desc',
            n_bars=10,
            fixed_order=False,
            fixed_max=True,
            steps_per_period=10,
            interpolate_period=False,
            label_bars=True,
            bar_size=.95,
            period_length=500,
            figsize=(5, 3),
            dpi=144,
            cmap='dark12',
            title='F1 2025 Driver Standings',
            bar_label_size=7,
            tick_label_size=7,
            shared_fontdict={'family': 'Helvetica', 'color': '.1'},
            scale='linear',
            writer='ffmpeg',
            fig=None,
            bar_kwargs={'alpha': .7},
            filter_column_colors=True
        )
        print("Animation saved to f1_2025_standings.mp4")
    except Exception as e:
        print(f"Animation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    animate()
