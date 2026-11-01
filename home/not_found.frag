#version 300 es
precision highp float;

in vec2 uv;
out vec4 color;

uniform sampler2D tex;
uniform float uTime;
uniform vec2 resolution;

const float SCALE = 228.0;
const float TONES = 165.0;

void main() {
    vec2 aspect = vec2(1.0, resolution.y / resolution.x);
    vec2 grid = uv * SCALE * aspect;
    vec2 cell = floor(grid);
    vec2 local = fract(grid) - 0.5;

    vec2 sampleUV = (cell + 0.5) / (SCALE * aspect);
    sampleUV.y = -sampleUV.y * 0.001 + uTime * 0.000634;
    sampleUV.x += uTime * 0.000523;

    vec3 source = texture(tex, sampleUV).rgb;
    float brightness = dot(source, vec3(0.299, 0.587, 0.114));
    float tone = clamp(floor(brightness * TONES) / (TONES - 1.0), 0.0, 1.0);

    float distance = abs(local.x) + abs(local.y);
    float radius = tone * 0.5;
    float edge = fwidth(distance);
    float mask = 1.0 - smoothstep(radius - edge, radius + edge, distance);

    color = vec4(source * mask, 1.0);
}
